import asyncio
import unittest

from .utils import FakeContext

class TestUtilityClasses(unittest.TestCase):
    def test_fake_ctx(self):
        ctx = FakeContext()
        self.assertFalse(ctx.send_called)
        self.assertIsNone(ctx.send_parameters)

        asyncio.run(ctx.send('foo'))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, 'foo')
