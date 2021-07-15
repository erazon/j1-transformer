import datetime
import hashlib
import json
import re

import xmltodict

gmtSuffixPattern=re.compile(r'\sGMT([+\-]\d+)$')

class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        else:
            return json.JSONEncoder.default(self, obj)


class Json:
    @staticmethod
    def dumps(data_dict, indent=None):
        return json.dumps(data_dict, cls=JsonEncoder, indent=indent,
                          ensure_ascii=False)


def xml_to_dict(xml_str):
    if xml_str is None or len(xml_str) == 0:
        return {}
    try:
        convertedDict = xmltodict.parse(xml_str)
    except xmltodict.expat.ExpatError:
        print("Xml parsing error")  # raise exception
        return {}
    return convertedDict


def convert_to_datetime(date_string):
    return datetime.datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S')


def get_utc_time():
    date_str = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    return convert_to_datetime(date_string=date_str)

def normalize_localized_gmt_date(dateStr):
    if dateStr is None:
        return None
    m = gmtSuffixPattern.search(dateStr)
    if m:
        return re.sub(gmtSuffixPattern, '', dateStr) + m.group(1)
    return dateStr

def string_to_md5(text):
    m = hashlib.md5()
    m.update(text.encode('utf-8'))
    return m.hexdigest()


d = {
    'A': 'Afjal',
    'D': datetime.datetime.now()
}

# print(type(Json.dumps(d, indent=2)))
# print(s3_bucket[0])
# print(type(s3_bucket))
# print(get_story_path("domain", "id"))
# print(path_suffix)
# print(s3_exists("ree"))
