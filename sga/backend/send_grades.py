""""
This module handles sending grades back to edX

Most of this module is a python 3 port of pylti (github.com/mitodl/sga-lti)
and should be moved back into that library.
"""

import uuid
import oauth2
from django.conf import settings
from xml.etree import ElementTree as etree


def send_grade(consumer_key, edx_url, result_id, grade):
    """ Sends a grade to edX """
    body = generate_request_xml(str(uuid.uuid1()), "replaceResult", result_id, grade)
    secret = settings.LTI_OAUTH_CREDENTIALS[consumer_key]
    response, content = _post_patched_request(consumer_key, secret, body, edx_url, "POST", "application/xml")
    print(response)
    print(content)


def _post_patched_request(lti_key, secret, body, url, method, content_type):
    """
    Authorization header needs to be capitalized for some LTI clients
    this function ensures that header is capitalized

    :param body: body of the call
    :param client: OAuth Client
    :param url: outcome url
    :return: response
    """

    consumer = oauth2.Consumer(key=lti_key, secret=secret)
    client = oauth2.Client(consumer)

    import httplib2

    http = httplib2.Http
    # pylint: disable=protected-access
    normalize = http._normalize_headers

    def my_normalize(self, headers):
        """ This function patches Authorization header """
        ret = normalize(self, headers)
        if 'authorization' in ret:
            ret['Authorization'] = ret.pop('authorization')
        return ret

    http._normalize_headers = my_normalize
    monkey_patch_function = normalize
    response, content = client.request(
        url,
        method,
        body=body.encode("utf8"),
        headers={'Content-Type': content_type})

    http = httplib2.Http
    # pylint: disable=protected-access
    http._normalize_headers = monkey_patch_function

    return response, content


def generate_request_xml(message_identifier_id, operation,
                         lis_result_sourcedid, score):
    # pylint: disable=too-many-locals
    """
    Generates LTI 1.1 XML for posting result to LTI consumer.

    :param message_identifier_id:
    :param operation:
    :param lis_result_sourcedid:
    :param score:
    :return: XML string
    """
    root = etree.Element('imsx_POXEnvelopeRequest',
                         xmlns='http://www.imsglobal.org/services/'
                               'ltiv1p1/xsd/imsoms_v1p0')

    header = etree.SubElement(root, 'imsx_POXHeader')
    header_info = etree.SubElement(header, 'imsx_POXRequestHeaderInfo')
    version = etree.SubElement(header_info, 'imsx_version')
    version.text = 'V1.0'
    message_identifier = etree.SubElement(header_info,
                                          'imsx_messageIdentifier')
    message_identifier.text = message_identifier_id
    body = etree.SubElement(root, 'imsx_POXBody')
    xml_request = etree.SubElement(body, '%s%s' % (operation, 'Request'))
    record = etree.SubElement(xml_request, 'resultRecord')

    guid = etree.SubElement(record, 'sourcedGUID')

    sourcedid = etree.SubElement(guid, 'sourcedId')
    sourcedid.text = lis_result_sourcedid
    if score is not None:
        result = etree.SubElement(record, 'result')
        result_score = etree.SubElement(result, 'resultScore')
        language = etree.SubElement(result_score, 'language')
        language.text = 'en'
        text_string = etree.SubElement(result_score, 'textString')
        text_string.text = score.__str__()
    ret = "<?xml version='1.0' encoding='utf-8'?>\n{}".format(
        etree.tostring(root, encoding='unicode'))

    return ret
