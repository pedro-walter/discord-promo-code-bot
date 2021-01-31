import asyncio
from datetime import datetime
import unittest
from unittest.mock import AsyncMock

from utils import validate_group_name, parse_codes_in_bulk, validate_code, sqlite_datetime_hack, send_long_message_array
from tests.utils import ReceivesMessages

class TestValidateGroupName(unittest.TestCase):
    def test_it_works(self):
        self.assertTrue(validate_group_name('ASDFasdf1234'))
        self.assertTrue(validate_group_name('ASDF_asdf-1234'))
        self.assertFalse(validate_group_name('adsf$qwer'))

class TestValidateCode(unittest.TestCase):
    def test_it_works(self):
        self.assertTrue(validate_code('ASDFasdf1234'))
        self.assertTrue(validate_code('ASDF-asdf-1234'))
        self.assertFalse(validate_code('adsf$qwer'))

class TestParseCodesInBulk(unittest.TestCase):
    def test_it_works(self):
        code_bulk = 'ASDF-1234 QWER-5678,ZXCV-9012, POIU-0987$#@ÇLKJ-7654'
        result = ['ASDF-1234', 'QWER-5678', 'ZXCV-9012', 'POIU-0987', 'ÇLKJ-7654']
        self.assertEqual(parse_codes_in_bulk(code_bulk), result)

class TestSQLiteDatetimeHack(unittest.TestCase):
    def test_parses_str(self):
        datetime_str = '2020-05-25 22:03:15.414286+00:00'
        dt = sqlite_datetime_hack(datetime_str)
        self.assertEqual(dt.__class__, datetime)

    def test_returns_datetime(self):
        now = datetime.now()
        result = sqlite_datetime_hack(now)
        self.assertEqual(now, result)

class TestSendLongMessageArray(unittest.TestCase):
    def test_just_sends_when_under_chunk_size(self):
        receives_messages = ReceivesMessages()

        asyncio.run(send_long_message_array(
            send_function=receives_messages.send,
            message="AbcDefg",
            chunk_size=20
        ))

        self.assertTrue(receives_messages.send_called)
        self.assertEqual(receives_messages.send_parameters, "AbcDefg")

    def test_splits_message_when_over_chunk_size(self):
        mock = AsyncMock(return_value=None)

        asyncio.run(send_long_message_array(
            send_function=mock,
            message="aaaaaaaaaaaaaaaaa-bbbbbbbbbbbbbbbbb",
            chunk_size=19,
            split_character='-'
        ))
        mock.assert_any_await("aaaaaaaaaaaaaaaaa\n\nPage 1/2")
        mock.assert_any_await("bbbbbbbbbbbbbbbbb\n\nPage 2/2")