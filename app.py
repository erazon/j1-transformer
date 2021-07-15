import argparse
import datetime
import logging
import os

from campuslibs.eventmanager import event_publisher
from campuslibs.eventmanager.event_generator import EventActions
from models.importer.base import ImporterStatus, ImporterExecutionStatus

from client import mongoengine_client
from config.config import Config
from transformer.transform import HigherReachTransformer
from services import mongodb_service

logger = logging.getLogger("app")
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
logger.propagate = False

parser = argparse.ArgumentParser(description='Transformer Runner')
parser.add_argument('--importer-id', type=str, required=True,
                    help='provide importer-id from mongodb(Ref)')
args = parser.parse_args()

EVENT_RESPONSE = {
    "success": False,
    "importer_id": None,
    "import_history_id": None,
    "msg": "Transformer not yet started"
}


def set_response(success=None, msg=None, import_history_id=None, importer_id=None):
    if success: EVENT_RESPONSE['success'] = success
    if msg: EVENT_RESPONSE['msg'] = msg
    if import_history_id: EVENT_RESPONSE['import_history_id'] = import_history_id
    if importer_id: EVENT_RESPONSE['importer_id'] = importer_id


def processed_base_url(base_url):
    root_phrase = "modules/shop"
    base = base_url.split(root_phrase)
    return os.path.join(base[0], root_phrase)


class Runner:
    def __init__(self, course_provider, transformer, config):
        self.tranformer = transformer
        self.course_provider = course_provider
        self.config = config
        self.transformer_start_time = datetime.datetime.utcnow()

    def run(self):
        try:
            new_course_ids, program_ids = self.tranformer.transform()
            logger.info(
                "{} courses updated/inserted".format(len(new_course_ids)))
            all_course_ids = mongodb_service.get_all_courses(
                course_provider=self.course_provider)
            logger.info("Total courses: {}".format(len(all_course_ids)))
            deleted_ids = list(set(all_course_ids).difference(set(
                new_course_ids)))
            logger.info("deleted courses: {}".format(len(deleted_ids)))

            if len(deleted_ids):
                logger.info(
                    "deleted mongodb ids: {}".format(", ".join(
                        str(x) for x in deleted_ids)))

            mongodb_service.delete_courses(
                course_list=deleted_ids
            )
            return len(new_course_ids)
        except Exception as error:
            raise error


def main():
    config = Config
    importer_id = args.importer_id
    logger.info("importer_id: {}".format(importer_id))

    try:
        mongoengine_client.connect_to_mongodb(config)
        import_history_id = mongodb_service.get_import_history_id(importer_id)
        logger.info("import-history-id: {}".format(import_history_id))
        set_response(import_history_id=import_history_id, importer_id=importer_id)

        course_provider = mongodb_service.get_course_provider(import_history_id)
        base_url = mongodb_service.get_base_url(import_history_id)
        base_url = processed_base_url(base_url)

        set_response(success=True, msg="Transforming Started")
        if Config.SEND_EVENT_MESSAGE:
            event_publisher.publish(EventActions.STARTED_TRANSFORMER.value, EVENT_RESPONSE)

        mongodb_service.update_importer_status(importer_id, ImporterStatus.RUNNING.value,
                                                ImporterExecutionStatus.TRANSFORM_STARTED.value)

        hr_transformer = HigherReachTransformer(
            import_history_id,
            course_provider,
            base_url
        )
        runner = Runner(
            course_provider=course_provider,
            transformer=hr_transformer,
            config=config
        )
        _ = runner.run()

        imp_status = ImporterStatus.READY.value if EVENT_RESPONSE.get('success', False) else ImporterStatus.ERROR.value
        mongodb_service.update_importer_status(importer_id, imp_status, ImporterExecutionStatus.TRANSFORM_DONE.value)
        set_response(success=True, msg="Transforming Completed")

    except Exception as e:
        logger.exception('Failed to run transformer! importer-id: %s Error: %s' % (importer_id, e))

        set_response(success=False, msg=str(e))
        mongodb_service.update_importer_status(importer_id, ImporterStatus.ERROR.value,
                                                ImporterExecutionStatus.TRANSFORM_DONE.value)
        mongodb_service.update_error(import_history_id, str(e))

    finally:
        if Config.SEND_EVENT_MESSAGE:
            event_publisher.publish(EventActions.COMPLETED_TRANSFORMER.value, EVENT_RESPONSE)

        mongoengine_client.disconnect_to_mongodb()
        logger.info("Done!")


if __name__ == '__main__':
    main()
