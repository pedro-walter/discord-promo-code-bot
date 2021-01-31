import asyncio
import logging

from main import add_group, remove_group, list_group
from model import PromoCodeGroup, PromoCode

from .utils import DBTestCase, FakeGuild2, FakeContext

logging.basicConfig(level=logging.ERROR)


class TestAddGroup(DBTestCase):
    def test_add_group(self):
        ctx = FakeContext()
        asyncio.run(add_group(ctx, group_name='foo'))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, "Grupo foo criado")

        group = PromoCodeGroup.get(
            (PromoCodeGroup.guild_id == ctx.guild.id)
            &
            (PromoCodeGroup.name == 'foo')
        )

        self.assertEqual(group.guild_id, ctx.guild.id)
        self.assertEqual(group.name, 'foo')

        ctx = FakeContext()
        asyncio.run(add_group(ctx, group_name='foo'))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, "Grupo já existente")

        ctx = FakeContext(guild=FakeGuild2())
        asyncio.run(add_group(ctx, group_name='foo'))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, "Grupo foo criado")

    def test_invalid_group_name(self):
        ctx = FakeContext()
        asyncio.run(add_group(ctx, group_name='asdf$'))

        self.assertTrue(ctx.send_called)
        self.assertEqual(
            ctx.send_parameters,
            "Nome de grupo inválido. Use apenas letras, números, traços (-) e underscore (_)" # noqa E501
        )


class TestRemoveGroup(DBTestCase):
    def test_group_exists(self):
        ctx = FakeContext()
        PromoCodeGroup.create(guild_id=ctx.guild.id, name='foo')

        asyncio.run(remove_group(ctx, group_name='foo'))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, "Grupo foo removido")

    def test_user_does_not_exist(self):
        ctx = FakeContext()
        asyncio.run(remove_group(ctx, group_name='foo'))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, "Grupo foo não existe!")

    def test_user_does_not_exist_in_this_guild(self):
        ctx = FakeContext()
        guild2 = FakeGuild2()
        PromoCodeGroup.create(guild_id=guild2.id, name='foo')
        asyncio.run(remove_group(ctx, group_name='foo'))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, "Grupo foo não existe!")

    def test_delete_group_removes_its_keys(self):
        ctx = FakeContext()
        group = PromoCodeGroup.create(guild_id=ctx.guild.id, name='foo')
        PromoCode.create(group=group, code='ASDF-1234')
        asyncio.run(remove_group(ctx, group_name='foo'))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, "Grupo foo removido")
        self.assertEqual(PromoCode.select().count(), 0)


class TestListUser(DBTestCase):
    def test_has_no_results(self):
        ctx = FakeContext()
        asyncio.run(list_group(ctx))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters,
                         "Não há grupos de código promocional cadastrados")

    def test_has_groups_in_different_guild(self):
        ctx = FakeContext()
        guild2 = FakeGuild2()
        PromoCodeGroup.create(guild_id=guild2.id, name='foo')
        asyncio.run(list_group(ctx))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters,
                         "Não há grupos de código promocional cadastrados")

    def test_has_results_in_same_guild(self):
        ctx = FakeContext()
        PromoCodeGroup.create(guild_id=ctx.guild.id, name='foo')

        asyncio.run(list_group(ctx))

        self.assertTrue(ctx.send_called)
        self.assertEqual(
            ctx.send_parameters,
            "Estes são os grupos de código promocional existentes: \n- foo"
        )
