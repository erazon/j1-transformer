import logging

from transformer import BaseMapperMixin
from utils.utils import normalize_localized_gmt_date

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class MeetingMapper(BaseMapperMixin):
    def __init__(self):
        pass

    def map(self, meeting):
        try:
            section_type = meeting.get("MeetingType", "")
            external_version_id = str(meeting.get("oca", 0))
            name = meeting.get("Name", "")
            description = meeting.get("Description")
            start_at = normalize_localized_gmt_date(meeting.get("StartDate"))
            end_at = normalize_localized_gmt_date(meeting.get("EndDate"))
            building_name = meeting.get("BuildingName")
            building_code = meeting.get("BuildingNumber")
            room_name = meeting.get("RoomName")
            return {
                "section_type": section_type,
                "external_version_id": external_version_id,
                "name": name,
                "description": description,
                "start_at": start_at,
                "end_at": end_at,
                "building_name": building_name,
                "building_code": building_code,
                "room_name": room_name
            }
        except Exception as error:
            raise error
