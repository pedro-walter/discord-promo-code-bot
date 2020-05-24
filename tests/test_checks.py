import asyncio

from main import is_authorized_or_owner
from model import AuthorizedUser

from .utils import DBTestCase, FakeGuild2, FakeContext, returns_true, returns_false

class TestIsAuthorizedOrOwner(DBTestCase):
    def test_owner_is_authorized(self):
        ctx = FakeContext()
        result = asyncio.run(is_authorized_or_owner(ctx, is_owner=returns_true))
        self.assertTrue(result)


    def test_user_is_authorized(self):
        ctx = FakeContext()
        AuthorizedUser.create(guild_id=ctx.guild.id, user_id=ctx.author.id)
        result = asyncio.run(is_authorized_or_owner(ctx, is_owner=returns_false))
        self.assertTrue(result)


    def test_user_is_not_authorized(self):
        ctx = FakeContext()
        result = asyncio.run(is_authorized_or_owner(ctx, is_owner=returns_false))
        self.assertFalse(result)


    def test_user_is_not_authorized_but_authorized_in_another_guild(self):
        ctx = FakeContext()
        guild2 = FakeGuild2()
        AuthorizedUser.create(guild_id=guild2.id, user_id=ctx.author.id)
        result = asyncio.run(is_authorized_or_owner(ctx, is_owner=returns_false))
        self.assertFalse(result)
