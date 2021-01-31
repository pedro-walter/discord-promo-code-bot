import asyncio
import logging

from main import add_user, remove_user, list_user
from model import AuthorizedUser

from .utils import (DBTestCase,
                    FakeUser,
                    FakeGuild2,
                    FakeContext,
                    fake_fetch_user)

logging.basicConfig(level=logging.ERROR)


class TestAddUser(DBTestCase):
    def test_add_user(self):
        ctx = FakeContext()
        user = FakeUser()
        asyncio.run(add_user(ctx, user=user))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, "Adicionado usuário foo")

        authorized_user = AuthorizedUser.get(
            (AuthorizedUser.guild_id == ctx.guild.id)
            &
            (AuthorizedUser.user_id == user.id)
        )

        self.assertEqual(authorized_user.user_id, user.id)

        ctx = FakeContext()
        asyncio.run(add_user(ctx, user=user))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, "Usuário já autorizado")

        ctx = FakeContext(guild=FakeGuild2())
        asyncio.run(add_user(ctx, user=user))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, "Adicionado usuário foo")


class TestRemoveUser(DBTestCase):
    def test_user_exists(self):
        user = FakeUser()
        ctx = FakeContext()
        AuthorizedUser.create(guild_id=ctx.guild.id, user_id=user.id)

        asyncio.run(remove_user(ctx, user=user))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters,
                         "Usuário {} desautorizado".format(user.name))

    def test_user_does_not_exist(self):
        user = FakeUser()
        ctx = FakeContext()
        asyncio.run(remove_user(ctx, user=user))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters,
                         "Usuário não estava autorizado: {}".format(user.name))

    def test_user_does_not_exist_in_this_guild(self):
        user = FakeUser()
        ctx = FakeContext()
        guild2 = FakeGuild2()
        AuthorizedUser.create(guild_id=guild2.id, user_id=user.id)
        asyncio.run(remove_user(ctx, user=user))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters,
                         "Usuário não estava autorizado: {}".format(user.name))


class TestListUser(DBTestCase):
    def test_has_no_results(self):
        ctx = FakeContext()
        asyncio.run(list_user(ctx, fetch_user=fake_fetch_user))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, "Não há usuários autorizados")

    def test_has_users_in_different_guild(self):
        ctx = FakeContext()
        guild2 = FakeGuild2()
        AuthorizedUser.create(guild_id=guild2.id, user_id=ctx.author.id)
        asyncio.run(list_user(ctx, fetch_user=fake_fetch_user))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, "Não há usuários autorizados")

    def test_has_results_in_same_guild(self):
        user = FakeUser()
        ctx = FakeContext()
        AuthorizedUser.create(guild_id=ctx.guild.id, user_id=user.id)

        asyncio.run(list_user(ctx, fetch_user=fake_fetch_user))

        self.assertTrue(ctx.send_called)
        self.assertEqual(
            ctx.send_parameters,
            "Estes são os usuários autorizados: \n- {}".format(user.name)
        )
