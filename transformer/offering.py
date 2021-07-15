import logging
import os

import slug

from transformer import BaseMapperMixin

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class OfferingMapper(BaseMapperMixin):
    def __init__(self, base_url, course_provider):
        self.course_provider = course_provider
        self.base_url = base_url

    def __get_external_url(self, item):
        URL = item.get("URL", None)
        return URL

    def __get_external_id(self, item):
        offering_id = item.get("OfferingID", None)
        return str(offering_id)

    def __get_external_version_id(self, item):
        version = item.get("oca", 0)
        return str(version)

    def __get_inquiry_url(self, base_url, offeringID):
        formater = "index.html?action=courseInquiry&OfferingID={}".format(
            offeringID)
        url = os.path.join(base_url, formater)
        return url

    def __get_slug(self, offering_id, title):
        title = title if title else ""
        text = str(offering_id) + " " + title
        course_slug = slug.slug(text)
        logger.debug("Slug: {}".format(course_slug))
        return course_slug

    def map(self, offering):
        from_importer = True
        external_id = self.__get_external_id(offering)
        external_url = self.__get_external_url(offering)
        external_version_id = self.__get_external_version_id(offering)

        code = offering.get("OfferingCode", "")
        title = offering.get("Name", "")
        course_slug = self.__get_slug(external_id, title)
        inquiry_url = self.__get_inquiry_url(
            base_url=self.base_url,
            offeringID=external_id
        )

        logger.debug("course-slug: {}".format(course_slug))
        description = offering.get("Description", "")
        if description is None:
            description = ""

        return {
            "provider": self.course_provider,
            "from_importer": from_importer,
            "external_id": external_id,
            "external_url": external_url,
            "inquiry_url": inquiry_url,
            "external_version_id": external_version_id,
            "code": code,
            "title": title,
            "slug": course_slug,
            "description": description,
            "programs": [],
        }
