import re

UUID_REGEX_RAW = r'[a-z0-9]{8}-(?:[a-z0-9]{4}-){3}[a-z0-9]{12}'
CDN_REGEX = re.compile(r'^https?://ucarecdn.com/(?P<file_id>'
                       + UUID_REGEX_RAW + r')/')
UUID_REGEX = re.compile(UUID_REGEX_RAW)


def parse_url_or_uuid(url_or_uuid):
    m = CDN_REGEX.match(url_or_uuid)

    if m:
        return url_or_uuid, m.group('file_id')

    m = UUID_REGEX.match(url_or_uuid)

    if m:
        return "https://ucarecdn.com/%s/" % m.group(0), m.group(0)

    raise ValueError('Neither URL nor UUID')


class ProcessedFile(object):
    def __init__(self, url_or_uuid):
        self.url, self.uuid = parse_url_or_uuid(url_or_uuid)



    def serialize(self):
        return self.url

