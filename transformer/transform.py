import logging

from models.course.course import Course
from models.course.section import Section
from models.course.section_schedule import SectionSchedule
from models.history.import_history import ImportHistoryDataKeys
from models.program.course_program import CourseProgram

from transformer import BaseTransformer, BaseMapperMixin
from transformer.offering import OfferingMapper
from transformer.programs import ProgramMapper
from transformer.sections import SectionMapper
from services import mongodb_service

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class HigherReachTransformer(BaseTransformer, BaseMapperMixin):

    def __init__(self, import_history_id, course_provider, base_url):
        super().__init__()
        self.import_history_id = import_history_id
        self.course_provider = course_provider
        self.base_url = base_url
        self.map_offering = OfferingMapper(
            base_url=base_url,
            course_provider=self.course_provider
        )
        self.map_program = ProgramMapper(
            base_url=base_url,
            course_provider=self.course_provider
        )
        self.map_section = SectionMapper(
            import_history_id=import_history_id,
            base_url=base_url,
            course_provider=self.course_provider
        )

    def __get_course_model(self, mapped_offering, mapped_sections):
        new_course = Course(**mapped_offering)
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
        new_course.sections = sections
        return new_course

    def __get_program_model(self, program_dict):
        program = CourseProgram(**program_dict)
        return program

    def __course_transform(self):
        logger.info("Course transformer running...!")
        try:
            new_course_ids = []
            history_data = mongodb_service.get_history_data(
                import_history_id=self.import_history_id,
                key_name=ImportHistoryDataKeys.offerings_overview
            )
            # Todo: check why cursor not found
            # import-history-id: 5e7213128e7d4ef3b33e0f77 importer_id: 5e71000f27d47bf3b3a6d1c8
            for idx, obj in enumerate(history_data):
                offering_overview = obj['data_object']
                offering_id = obj['data_object_id']
                logger.info("#############################")
                logger.info("IDX: {} | Offering_id: {}".format(
                    idx, offering_id))

                mapped_offering = self.map_offering.map(offering_overview)
                sections_obj = mongodb_service.get_history_data(
                    import_history_id=self.import_history_id,
                    key_name=ImportHistoryDataKeys.sections,
                    external_key="OfferingID",
                    external_id=offering_id
                )
                mapped_sections = self.map_section.map(sections_obj)
                if len(mapped_sections) == 0:
                    mapped_offering['is_published'] = False
                    mapped_offering['published_by'] = None

                course_id = mongodb_service.two_phase_course_update(
                    mapped_offering=mapped_offering,
                    mapped_sections=mapped_sections
                )
                new_course_ids.append(course_id)

            logger.info("Course transformer is Done!")
            return new_course_ids

        except Exception as error:
            raise error

    def __program_transform(self):
        logger.info("Program transformer running...!")
        try:
            program_ids = []
            history_data = mongodb_service.get_history_data(
                import_history_id=self.import_history_id,
                key_name=ImportHistoryDataKeys.programs_detail
            )
            for obj in history_data:
                program_id = obj['data_object_id']
                logger.info("program_id: {}".format(program_id))
                program = obj['data_object']
                mapped_program = self.map_program.map(program)

                offering_ids = self.map_program.get_offeringids(program)
                logger.info("program_id: {} courses found: {}".format(
                    mapped_program['external_id'], len(offering_ids)))
                logger.info("OfferingIDS: {}".format(
                    ", ".join(map(str, offering_ids))))

                program_obj = mongodb_service.two_phase_program_update(
                    mapped_program=mapped_program,
                    offering_ids=offering_ids
                )
                program_ids.append(program_obj.id)

            logger.info("Program transformer is Done!")
            return program_ids
        except Exception as error:
            raise error

    def transform(self, import_history_id=None):
        try:
            new_course_ids = self.__course_transform()
            logger.info("Total course count: {}".format(len(new_course_ids)))

            program_ids = self.__program_transform()
            logger.info("Total {} programs found!".format(len(program_ids)))
            return new_course_ids, program_ids
        except Exception as error:
            raise error
