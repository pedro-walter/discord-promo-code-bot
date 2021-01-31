import asyncio
import unittest

from .utils import FakeContext
from main import echo


class TestEcho(unittest.TestCase):
    def test_echo(self):
        ctx = FakeContext()
        asyncio.run(echo(ctx, 'foo'))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, 'foo')
