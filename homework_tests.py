from unittest import TestCase, mock, main as uni_main
from homework import *

JSON_ERROR = {'error': 'testing'}
JSON_HW_ERROR = {'homeworks': [{'homework_name': 'test', 'status': 'test'}]}
JSON_HW_STRUCTURE = {'homeworks': 1}

ReqEx = requests.RequestException


class TestReq(TestCase):
    @mock.patch('requests.get')
    def test_json(self, rq_get):
        resp = mock.Mock()
        resp.status_code  = 200
        resp.json = mock.Mock(return_value=JSON_HW_STRUCTURE)
        rq_get.return_value = resp
        main()
uni_main()


def unused():
    def test_raised(self, rq_get):
        rq_get.side_effect = mock.Mock(side_effect=ReqEx('testing'))
        main()

    def test_json(self, rq_get):
        resp = mock.Mock()
        resp.status_code  = 200
        resp.json = mock.Mock(return_value=JSON_ERROR)
        rq_get.return_value = resp
        main()

    def test_status_code(self, rq_get):
        resp = mock.Mock()
        resp.status_code  = 666
        rq_get.return_value = resp
        main()