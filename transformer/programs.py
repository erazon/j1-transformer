import logging
import os

from models.course.course_fee import CourseFee

from transformer import BaseMapperMixin
from utils.utils import normalize_localized_gmt_date

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class ProgramMapper(BaseMapperMixin):
    def __init__(self, base_url, course_provider):
        self.base_url = base_url
        self.course_provider = course_provider

    def __get_external_url(self, base_url, program_id):
        url = os.path.join(base_url, "programDetail.action?" + "programID={}")
        url = url.format(program_id)
        return url

    def __get_external_version_id(self, program):
        return program.get("oca", 0)

    def __get_enrollment_fee(self, program):
        amount = program.get("EnrollmentFee", None)
        amount = float(amount) if amount else 0.0
        fee = CourseFee(
            amount=amount,
            currency="USD"
        )
        return fee

    def __get_application_fee(self, program):
        amount = program.get("ApplicationFee", None)
        amount = float(amount) if amount else 0.0
        fee = CourseFee(
            amount=amount,
            currency="USD"
        )
        return fee

    def transform_to_list(self, data):
        data = [] if data is None else data
        data = [data] if isinstance(data, dict) else data
        return data

    def get_offeringids(self, program):
        try:
            offering_blocks = program.get("ProgramReqGroups") if program.get(
                "ProgramReqGroups", None) else {}
            offering_blocks = offering_blocks.get(
                "ProgramReqGroup") if offering_blocks.get("ProgramReqGroup",
                                                          None) else {}
            offering_blocks = self.transform_to_list(offering_blocks)

            offering_ids = []
            for offering_block in offering_blocks:
                offering_block = offering_block.get(
                    "Offerings") if offering_block.get("Offerings",
                                                       None) else {}
                offering_block = offering_block.get(
                    "Offering") if offering_block.get("Offering", None) else {}
                offering_block = self.transform_to_list(offering_block)
                for offering in offering_block:
                    offering_id = offering.get("OfferingID")
                    offering_ids.append(offering_id)
            return offering_ids
        except AttributeError as error:
            logger.info(program)
            raise error

    def map(self, program):
        """
        about:
        external_url (not found URL for program)
        RequirementDescription (not in model) try:
            program_id = 56 hid = ObjectId("5e1251d3e268d2fdef0d1e66")

        :param program:
        :return:
        """
        name = program.get("Name", "")
        code = program.get("ProgramCode", "")
        status_name = program.get("ProgramStatusName", "")
        external_id = program.get("ProgramID", "")
        external_url = self.__get_external_url(base_url=self.base_url,
                                               program_id=external_id)
        external_version_id = self.__get_external_version_id(program)
        description = program.get("Description", "")

        enrollment_start_date = normalize_localized_gmt_date(program.get("EnrollmentStartDate", None))
        enrollment_end_date = normalize_localized_gmt_date(program.get("EnrollmentEndDate", None))
        start_date = normalize_localized_gmt_date(program.get("ProgramStartDate", None))
        department = program.get("DepartmentName", None)
        certificate_name = program.get("CertificateName", "")

        enrollment_enabled = bool(program.get("IsEnrollmentOn", None))
        application_required = bool(program.get("HasApplicationProcess", None))
        application_enabled = bool(program.get("IsApplicationOn", None))

        application_fee = self.__get_application_fee(program)
        enrollment_fee = self.__get_enrollment_fee(program)
        seat_capacity = program.get("SeatCapacity", None)

        return {
            "provider": self.course_provider,
            "name": name,
            "code": code,
            "status_name": status_name,
            "external_id": external_id,
            "external_url": external_url,
            "external_version_id": external_version_id,
            "description": description,

            "enrollment_start_date": enrollment_start_date,
            "enrollment_end_date": enrollment_end_date,
            "start_date": start_date,
            "department": department,
            "certificate_name": certificate_name,
            "enrollment_enabled": enrollment_enabled,
            "application_required": application_required,
            "application_enabled": application_enabled,

            "application_fee": application_fee,
            "enrollment_fee": enrollment_fee,
            "seat_capacity": seat_capacity,
        }
