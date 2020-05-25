import unittest

from utils import validate_group_name

class TestValidateGroupName(unittest.TestCase):
    def test_it_works(self):
        self.assertTrue(validate_group_name('ASDFasdf1234'))
        self.assertTrue(validate_group_name('ASDF_asdf-1234'))
        self.assertFalse(validate_group_name('adsf$qwer'))
