import logging
from copy import copy

from bson import ObjectId
from models.course.course import Course
from models.course.section import Section
from models.course.section_schedule import SectionSchedule
from models.courseprovider.instructor import Instructor
from models.history.import_history import ImportHistory, ImportHistoryData
from models.importer import HigherReachImporterConfig
from models.program.course_program import CourseProgram
from mongoengine import DoesNotExist, NotUniqueError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


def update_importer_status(importer_id, importer_status, imp_execution_status):
    try:
        importer_obj = HigherReachImporterConfig.objects(id=importer_id).get()
        importer_obj.status = importer_status
        importer_obj.execution_status = imp_execution_status
        importer_obj.save()
    except Exception as error:
        raise error


def update_error(import_history_id, error_msg):
    try:
        importer_history_obj = ImportHistory.objects(id=import_history_id).get()
        importer_history_obj.error = {'msg': error_msg}
        importer_history_obj.save()
        return importer_history_obj
    except DoesNotExist as e:
        raise e
    except Exception as e:
        raise e


def get_import_history_id(importer_id):
    try:
        last_import_history = HigherReachImporterConfig.objects.get(
            id=importer_id).last_import_history.id
        return last_import_history
    except Exception as error:
        raise error


def get_course_provider(import_history_id):
    try:
        provider = ImportHistory.objects.get(
            id=import_history_id).importer_config.course_provider
        return provider
    except Exception as error:
        raise error


def get_import_history(import_history_id):
    try:
        history = ImportHistory.objects.get(id=import_history_id)
        return history
    except Exception as error:
        raise error


def get_base_url(import_history_id):
    try:
        base_url = ImportHistory.objects.get(id=import_history_id).base_url
        return base_url
    except Exception as error:
        raise error


def check_instractor(name, external_id):
    if not (name and external_id):
        return None
    try:
        mongo_obj = Instructor.objects.get(
            name=name, external_id=str(external_id))
        return mongo_obj
    except DoesNotExist:
        return None

# previous code: cursor not found
# def get_history_data(import_history_id, key_name, external_key=None,
#                      external_id=None):
#     try:
#         params = {
#             "history": ObjectId(import_history_id),
#             "key_name": key_name,
#         }
#         if external_id and external_key:
#             key = "data_object__{}".format(external_key)
#             value = str(external_id)
#             params[key] = value
#         result = ImportHistoryData.objects.filter(**params)
#         return result
#     except DoesNotExist as e:
#         raise e
#     except Exception as e:
#         raise e


# fix code: cursor not found
def get_history_data(import_history_id, key_name, external_key=None,
                     external_id=None):
    try:
        params = [
            {"history": ObjectId(import_history_id)},
            {"key_name": key_name},
        ]
        if external_id and external_key:
            key = "data_object.{}".format(external_key)
            value = str(external_id)
            params.append({key:value})

        pipeline = [
            {"$match": {
                "$and": params
            }}
        ]

        for item in ImportHistoryData.objects().timeout(False).aggregate(*pipeline):
            yield item
    except DoesNotExist as e:
        raise e
    except Exception as e:
        raise e


# TODO convert it to two-phase-opp
def two_phase_program_update(mapped_program, offering_ids):
    try:
        provider = mapped_program.get("provider")
        offering_ids = [str(x) for x in offering_ids]
        course_objs = Course.objects(provider=provider, external_id__in=offering_ids).timeout(False)

        try:
            external_id = mapped_program.get("external_id")
            program_obj = CourseProgram.objects.get(provider=provider,
                                                    external_id=external_id)

        except DoesNotExist:
            program_obj = CourseProgram()

        for attr, value in mapped_program.items():
            program_obj.__setattr__(attr, value)

        program_obj.courses = course_objs
        program_obj.save()

        for course_obj in course_objs:
            course_obj.update(add_to_set__programs=program_obj)
        return program_obj
    except Exception as error:
        raise error


# TODO convert it to phase update
def two_phase_course_update(mapped_offering, mapped_sections):
    try:
        provider = mapped_offering.get("provider")
        sections = []
        for section in mapped_sections:
            sectionSchedules = section.get("schedules", [])
            schedules = []
            for schedule in sectionSchedules:
                new_sectionSchedule = SectionSchedule(**schedule)
                schedules.append(new_sectionSchedule)
            if "schedules" in section:
                del section['schedules']
            new_section = Section(**section)
            new_section.schedules = schedules
            sections.append(new_section)
        mapped_offering['sections'] = sections
        external_id = mapped_offering.get("external_id")
        try:
            logger.info("ExternalID: ----> {}".format(external_id))
            course_obj = Course.objects.get(
                external_id=external_id,
                provider=provider
            )
            _old = copy(course_obj.__dict__)
            for key, value in mapped_offering.items():
                course_obj.__setattr__(key, value)
            up_course_obj = course_obj.save(
                signal_kwargs={
                    "old": _old,
                    "update": mapped_offering
                })
            return up_course_obj.id
        except NotUniqueError:
            logger.warning(
                "Update! NotUniqueError for offeringID: {}".format(external_id))
        except DoesNotExist:
            logger.info("Does not exists")
            try:
                new_course = Course(**mapped_offering)
                ins_course_obj = new_course.save()
                return ins_course_obj.id
            except NotUniqueError:
                logger.warning(
                    "Insert! NotUniqueError for offeringID: {}".format(
                        external_id))

    except Exception as error:
        raise error


def get_all_courses(course_provider):
    try:
        objs = Course.objects(provider=course_provider).timeout(False)
        ids = []
        for data in objs:
            ids.append(data.id)
        return ids
    except Exception as e:
        raise e


def delete_courses(course_list):
    for course_id in course_list:
        try:
            del_obj = Course.objects.get(_id=ObjectId(course_id))
            del_obj.delete()
        except DoesNotExist:
            logger.warning("courseid: {} DoesNotExist for delete!".format(
                str(course_id)))
    pass
