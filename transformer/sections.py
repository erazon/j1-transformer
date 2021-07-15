import logging
import os

from models.course.course_fee import CourseFee
from models.course.enums import CreditUnits, ExecutionModes
from models.courseprovider.instructor import Instructor
from models.courseprovider.provider_site import CourseProviderSite
from models.history.import_history import ImportHistoryDataKeys
from mongoengine import DoesNotExist

from transformer import BaseMapperMixin
from transformer.meetings import MeetingMapper
from services import mongodb_service
from utils.utils import normalize_localized_gmt_date

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class SectionMapper(BaseMapperMixin):

    def __init__(self, import_history_id, course_provider, base_url):
        self.import_history_id = import_history_id
        self.base_url = base_url
        self.course_provider = course_provider
        self.map_meeting = MeetingMapper()

    def __get_registration_url(self, base_url, offeringID, sectionID):
        formater = "index.html?action=section&OfferingID={}&SectionID={}".format(
            offeringID, sectionID)
        url = os.path.join(base_url, formater)
        return url

    def __get_inquiry_url(self, base_url, offeringID):
        formater = "index.html?action=courseInquiry&OfferingID={}".format(
            offeringID)
        url = os.path.join(base_url, formater)
        return url

    def __get_num_seats(self, section):
        res = section.get("DefaultSeatGroup") if section.get(
            "DefaultSeatGroup") else {}
        res = res.get("SeatGroup") if res.get("SeatGroup") else {}
        res = res.get("NumberOfSeats")
        return res

    def __get_available_seats(self, section):
        res = section.get("DefaultSeatGroup") if section.get(
            "DefaultSeatGroup") else {}
        res = res.get("SeatGroup") if res.get("SeatGroup") else {}
        res = res.get("AvailableSeats", 0)
        return res

    def __is_online_location(self, site_name):
        if not site_name or not isinstance(site_name, str):
            return True
        online_location_names = ["ONLINE"] # all names should be in upper case
        return site_name.upper() in online_location_names

    def __get_execution_site(self, section, course_provider_id):

        is_distance_learning = section.get("IsDistanceLearning", False)

        if isinstance(is_distance_learning, str):
            is_distance_learning = True if is_distance_learning.lower() == "true" else False

        if is_distance_learning:
            return []

        res = section.get("Locations") if section.get("Locations") else {}
        res = res.get("Location") if res.get("Location") else {}
        locations = self.transform_to_list(res)
        course_provider_site_objs = []

        for location in locations:
            site_name = location.get("SiteName", None)
            if self.__is_online_location(site_name):
                continue
            try:
                mongo_obj = CourseProviderSite.objects.get(
                    name=site_name)
                course_provider_site_objs.append(mongo_obj)
            except DoesNotExist:
                course_provider_site = CourseProviderSite(
                    name=site_name,
                    provider=course_provider_id
                )
                course_provider_site.save()
                course_provider_site_objs.append(course_provider_site)
        return course_provider_site_objs

    def __get_instructors(self, section, course_provider_id):
        try:
            instructors = section.get("Instructors") if \
                section.get("Instructors", None) else {}
            instructors = instructors.get("Instructor") if instructors.get(
                "Instructor", None) else []
            instructors = self.transform_to_list(instructors)

            mongo_objs = []
            for instractor in instructors:
                name = instractor.get("InstructorName", None)
                external_id = instractor.get("FacultyID", "")
                if not (name and external_id):
                    return []
                instractor_obj = mongodb_service.check_instractor(
                    name=name, external_id=external_id)
                if instractor_obj:
                    mongo_objs.append(instractor_obj)
                else:
                    instractor = Instructor(
                        name=name,
                        external_id=str(external_id),
                        provider=course_provider_id
                    )
                    instractor.save()
                    mongo_objs.append(instractor)
            return mongo_objs

        except AttributeError as error:
            raise error
        except Exception as error:
            raise error

    def __get_course_fee(self, section):
        res = section.get("DefaultSeatGroup") if section.get(
            "DefaultSeatGroup") else {}
        res = res.get("SeatGroup") if res.get("SeatGroup") else {}
        res = res.get("Cost")

        # res = res.get("Charges") if res.get("Charges") else {}
        # res = res.get("Charge") if res.get("Charge") else {}
        # res = res.get("ItemUnitAmount")

        amout = 0.0
        if res:
            amout = float(res)
        fee = CourseFee(
            amount=amout,
            currency="USD"
        )
        return fee

    def __get_ceu_hours(self, section):
        value = section.get("CEUHours", None)
        if value:
            return float(value)
        return 0.0

    def __get_credits_hour(self, section):
        value = section.get("CreditHours", None)
        if value:
            return float(value)
        return 0.0

    def __get_clock_hours(self, section):
        value = section.get("ClockHours", None)
        if value:
            return float(value)
        return 0.0

    def __get_load_hours(self, section):
        value = section.get("LoadHours", None)
        if value:
            return float(value)
        return 0.0

    def __get_credits_info(self, section):
        ceu_hours = section.get("CEUHours")
        credits_hour = section.get("CreditHours")
        clock_hours = section.get("ClockHours")
        load_hours = section.get("LoadHours")

        if ceu_hours:
            return float(ceu_hours), CreditUnits.CEU_HOURS.value
        if credits_hour:
            return float(credits_hour), CreditUnits.CREDIT_HOURS.value

        if clock_hours:
            return float(clock_hours), CreditUnits.CLOCK_HOURS.value
        if load_hours:
            return float(load_hours), CreditUnits.LOAD_HOURS.value
        return None, None

    def __get_execution_mode(self, section, start_date, end_date):
        if start_date and end_date:
            return ExecutionModes.INSTRUCTOR_LED.value
        else:
            return ExecutionModes.SELF_PACED.value

    def __section_map(self, section):
        code = section.get("SectionNumber")
        external_version_id = str(section.get("oca", 0))
        description = section.get("Description")

        offeringID = section.get("OfferingID")
        sectionID = section.get("SectionID")
        logger.debug("SectionID: {}".format(sectionID))
        registration_url = self.__get_registration_url(
            base_url=self.base_url,
            offeringID=offeringID,
            sectionID=sectionID
        )
        inquiry_url = self.__get_inquiry_url(base_url=self.base_url,
                                             offeringID=offeringID)
        start_date = normalize_localized_gmt_date(section.get("StartDate"))
        end_date = normalize_localized_gmt_date(section.get("EndDate"))
        num_seats = self.__get_num_seats(section)
        available_seats = self.__get_available_seats(section)
        is_active = section.get("IsActive")

        execution_mode = self.__get_execution_mode(
            section, start_date,
            end_date
        )
        execution_site = self.__get_execution_site(
            section=section,
            course_provider_id=self.course_provider
        )

        logger.debug("excution site len: {}".format(len(execution_site)))
        if len(execution_site) > 0:  # TODO changed shared model to get list
            execution_site = execution_site[0]
        else:
            execution_site = None

        registration_deadline = normalize_localized_gmt_date(section.get("FinalEnrollmentDate"))
        instructors = []
        if execution_mode == ExecutionModes.INSTRUCTOR_LED.value:
            instructors = self.__get_instructors(
                section, self.course_provider.id)

        course_fee = self.__get_course_fee(section)
        credit_hours = self.__get_credits_hour(section)
        ceu_hours = self.__get_ceu_hours(section)
        clock_hours = self.__get_clock_hours(section)
        load_hours = self.__get_load_hours(section)

        # total_credits, credit_unit = self.__get_credits_info(section)

        section = {
            "code": code,
            "external_version_id": external_version_id,
            "description": description,
            "registration_url": registration_url,
            "inquiry_url": inquiry_url,
            "start_date": start_date,
            "end_date": end_date,
            "num_seats": num_seats,
            "available_seats": available_seats,
            "is_active": is_active,
            "execution_mode": execution_mode,
            "execution_site": execution_site,

            "registration_deadline": registration_deadline,
            "instructors": instructors,

            "course_fee": course_fee,
            "credit_hours": credit_hours,
            "ceu_hours": ceu_hours,
            "clock_hours": clock_hours,
            "load_hours": load_hours

            # "credit_unit": credit_unit,
            # "total_credits": total_credits,
        }
        return section

    def map(self, sections_obj):
        try:
            mapped_sections = []
            for obj in sections_obj:
                section = obj['data_object']
                section_id = obj['data_object_id']
                logger.info("section_id: {}".format(section_id))
                mapped_section = self.__section_map(section=section)

                meetings_obj = mongodb_service.get_history_data(
                    import_history_id=self.import_history_id,
                    key_name=ImportHistoryDataKeys.meetings,
                    external_key="SectionID",
                    external_id=section_id
                )

                mapped_meetings = []
                for mobj in meetings_obj:
                    meeting = mobj['data_object']
                    logger.info("meeting_id: {}".format(mobj['data_object_id']))
                    mapped_meeting = self.map_meeting.map(meeting)
                    mapped_meetings.append(mapped_meeting)
                mapped_section["schedules"] = mapped_meetings
                mapped_sections.append(mapped_section)
                logger.info("-----------------------------")
            return mapped_sections

        except Exception as error:
            raise error
