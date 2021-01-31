import asyncio
import unittest

from .utils import ReceivesMessages


class TestUtilityClasses(unittest.TestCase):
    def test_receives_messages_class(self):
        receives_messages = ReceivesMessages()
        self.assertFalse(receives_messages.send_called)
        self.assertIsNone(receives_messages.send_parameters)

        asyncio.run(receives_messages.send('foo'))

        self.assertTrue(receives_messages.send_called)
        self.assertEqual(receives_messages.send_parameters, 'foo')
