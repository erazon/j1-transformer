from models.course.course import Course
from models.history.import_history import ImportHistoryDataKeys

from client.mongoengine_client import connect_to_mongodb
from config.config import Config
from services import mongodb_service

connect_to_mongodb(Config)


# offering_ids = ['971', '973', '972', '374', '259', '272', '935', '98', '97',
#                 '200', '277', '58', '186', '13', '303']
#
# offering_ids = ["18", "19", "20"]
# offering_ids = [str(x) for x in offering_ids]
# print("offering_ids: %s" % offering_ids)
#
# # course_objs = Course.objects(external_id__in=["971", "973"])
# course_objs = Course.objects(external_id__in=offering_ids)
# print(course_objs)


def data_loader_test():
    import_history_id = "5e32b39d35536995c8b8f4d9"
    offering_id = 17124
    history_data = mongodb_service.get_history_data(
        import_history_id=import_history_id,
        key_name=ImportHistoryDataKeys.meetings,
        external_key="SectionID",
        external_id=offering_id
    )
    for idx, data_obj in enumerate(history_data):
        # print("IDX: %s obj: %s" % (idx, data_obj.to_json()))
        print("IDX: %s data_object_id: %s" % (idx, data_obj['data_object_id']))
        print("*" * 50)
    pass


data_loader_test()
