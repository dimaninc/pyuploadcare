import unittest

from mock import patch

from pyuploadcare import UploadCare, UploadCareException
from pyuploadcare.file import File


class MockResponse():
    def __init__(self, status, data):
        self.status = status
        self.data = data

    def read(self):
        return self.data


class UploadCareTest(unittest.TestCase):

    @patch('httplib.HTTPConnection', autospec=True)
    def test_raises(self, con):
        con.return_value.getresponse.return_value = MockResponse(404, '{}')
        ucare = UploadCare('pub', 'secret')

        with self.assertRaises(UploadCareException):
            ucare.make_request('GET', '/files/')

        con.return_value.getresponse.return_value = MockResponse(200, 'meh')
        with self.assertRaises(ValueError):
            ucare.make_request('GET', '/files/')

    @patch('httplib.HTTPConnection', autospec=True)
    def test_request_headers(self, con):
        def request_v01(verb, uri, content, headers):
            self.assertIn('Accept', headers)
            self.assertIn('User-Agent', headers)
            self.assertEqual(headers['Accept'], 'application/json')
            self.assertEqual(headers['User-Agent'], 'pyuploadcare/0.7')

        def request_v02(verb, uri, content, headers):
            self.assertIn('Accept', headers)
            self.assertIn('User-Agent', headers)
            self.assertEqual(headers['Accept'],
                             'application/vnd.uploadcare-v0.2+json')
            self.assertEqual(headers['User-Agent'], 'pyuploadcare/0.7')

        con.return_value.getresponse.return_value = MockResponse(200, '[]')
        con.return_value.request = request_v02

        ucare = UploadCare('pub', 'secret')
        ucare.make_request('GET', '/files/')

        con.return_value.request = request_v01
        ucare = UploadCare('pub', 'secret', api_version='0.1')
        ucare.make_request('GET', '/files/')

    def test_uri_builder(self):
        ucare = UploadCare('pub', 'secret')
        uri = ucare._build_uri('/files/?asd=1')
        self.assertEqual(uri, '/files/?asd=1')
        ucare = UploadCare('pub', 'secret', api_base='http://example.com/api')
        uri = ucare._build_uri('/files/?asd=1')
        self.assertEqual(uri, '/api/files/?asd=1')


class FileTest(unittest.TestCase):
    @patch('httplib.HTTPConnection', autospec=True)
    def test_keep_timeout(self, con):
        ucare = UploadCare('pub', 'secret')
        response = MockResponse(200, '{"on_s3": false}')
        con.return_value.getresponse.return_value = response

        f = File('uuid', ucare)
        with self.assertRaises(Exception) as cm:
            f.keep(wait=True, timeout=1)
        self.assertEqual('timed out trying to claim keep',
                         cm.exception.message)

        response = MockResponse(200, '{"on_s3": true}')
        con.return_value.getresponse.return_value = response
        f.keep(wait=True, timeout=1)

    @patch('httplib.HTTPConnection', autospec=True)
    def test_url_caching(self, con):
        """Test that known url is cached and no requests are made"""

        ucare = UploadCare('pub', 'secret')
        uuid = '6c5e9526-b0fe-4739-8975-72e8d5ee6342'
        con.return_value.getresponse.return_value = MockResponse(200,
            '{"original_file_url": "meh"}')

        self.assertEqual(0, len(con.mock_calls))

        f = ucare.file(uuid)
        self.assertEqual('meh', f.url)
        # 3 calls made (create con, request, get response)
        self.assertEqual(3, len(con.mock_calls))

        fake_url = 'http://i-am-the-file/{}/'.format(uuid)
        f = ucare.file(fake_url)
        self.assertEqual(fake_url, f.url)
        # no additional calls are made
        self.assertEqual(3, len(con.mock_calls))