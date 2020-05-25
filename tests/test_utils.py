import unittest

from utils import validate_group_name, parse_codes_in_bulk

class TestValidateGroupName(unittest.TestCase):
    def test_it_works(self):
        self.assertTrue(validate_group_name('ASDFasdf1234'))
        self.assertTrue(validate_group_name('ASDF_asdf-1234'))
        self.assertFalse(validate_group_name('adsf$qwer'))

class TestParseCodesInBulk(unittest.TestCase):
    def test_it_works(self):
        code_bulk = 'ASDF-1234 QWER-5678,ZXCV-9012, POIU-0987$#@ÇLKJ-7654'
        result = ['ASDF-1234', 'QWER-5678', 'ZXCV-9012', 'POIU-0987', 'ÇLKJ-7654']
        self.assertEqual(parse_codes_in_bulk(code_bulk), result)
