import bson
import mongoengine
from models.course.course import Course
from models.history.import_history import ImportHistoryData

from config.config import Config


def mongodb_connection():
    mongoengine.connect(
        db=Config.MONGODB_DATABASE,
        host=Config.MONGODB_HOST,
        port=Config.MONGODB_PORT,
        username=Config.MONGODB_USERNAME,
        password=Config.MONGODB_PASSWORD,
        authentication_source=Config.MONGODB_AUTH_DATABASE
    )


def get_id_from_history(key_name, import_history_id):
    importer_history_obj = ImportHistoryData.objects(
        history=bson.ObjectId(import_history_id),
        key_name=key_name,
    )
    ids = []
    for data in importer_history_obj:
        ids.append(data.data_object_id)
    return ids


def get_id_from_course(provider_id):
    objs = Course.objects(
        provider=provider_id
    )
    ids = []
    for data in objs:
        ids.append(data.external_id)
    return ids


def main():
    mongodb_connection()
    import_history_id = "5e459730875e3995b27bc197"
    provider_id = "5e4593c58361956859c99bb6"
    history_ids = get_id_from_history(
        key_name="offerings",
        import_history_id=import_history_id
    )
    print("#history-id: ", len(history_ids))
    course_ids = get_id_from_course(provider_id=provider_id)
    print("#course-id: ", len(course_ids))

    missing_ids = set(history_ids).difference(set(course_ids))
    print("#missing-ids: ", len(missing_ids))
    print("Missing ids: ", missing_ids)


if __name__ == '__main__':
    main()
