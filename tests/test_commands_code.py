import asyncio
import logging

from main import add_code, remove_code, list_code
from model import PromoCodeGroup, PromoCode

from .utils import DBTestCase, FakeContext, FakeGuild2

logging.basicConfig(level=logging.ERROR)

class TestAddCode(DBTestCase):
    def test_group_does_not_exist(self):
        ctx = FakeContext()
        asyncio.run(add_code(ctx, group_name='foo', code='ASDF-1234'))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, "Grupo de códigos promocionais não encontrado: foo")

    def test_group_exists_in_this_guild(self):
        ctx = FakeContext()
        PromoCodeGroup.create(guild_id=ctx.guild.id, name='foo')
        asyncio.run(add_code(ctx, group_name='foo', code='ASDF-1234'))

        self.assertTrue(ctx.send_called)
        self.assertEqual(
            ctx.send_parameters,
            "Código ASDF-1234 cadastrado no grupo foo com sucesso!"
        )

    def test_group_does_not_exist_in_this_guild(self):
        ctx = FakeContext()
        guild2 = FakeGuild2()
        PromoCodeGroup.create(guild_id=guild2.id, name='foo')
        asyncio.run(add_code(ctx, group_name='foo', code='ASDF-1234'))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, "Grupo de códigos promocionais não encontrado: foo")

    def test_code_already_registered(self):
        ctx = FakeContext()
        group = PromoCodeGroup.create(guild_id=ctx.guild.id, name='foo')
        PromoCode.create(group=group, code="ASDF-1234")
        asyncio.run(add_code(ctx, group_name='foo', code='ASDF-1234'))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, "Código ASDF-1234 já cadastrado no grupo foo")

class TestRemoveCode(DBTestCase):
    def test_code_does_not_exist(self):
        ctx = FakeContext()
        asyncio.run(remove_code(ctx, group_name='foo', code='ASDF-1234'))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, "Código ASDF-1234 não encontrado no grupo foo")

    def test_code_exists_in_another_guild(self):
        ctx = FakeContext()
        guild2 = FakeGuild2()
        group = PromoCodeGroup.create(guild_id=guild2.id, name='foo')
        PromoCode.create(group=group, code="ASDF-1234")
        asyncio.run(remove_code(ctx, group_name='foo', code='ASDF-1234'))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, "Código ASDF-1234 não encontrado no grupo foo")

    def test_code_exists_in_current_guild(self):
        ctx = FakeContext()
        group = PromoCodeGroup.create(guild_id=ctx.guild.id, name='foo')
        PromoCode.create(group=group, code="ASDF-1234")
        asyncio.run(remove_code(ctx, group_name='foo', code='ASDF-1234'))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, "Código ASDF-1234 excluído do grupo foo")

class TestListCode(DBTestCase):
    def test_group_does_not_exist(self):
        ctx = FakeContext()
        asyncio.run(list_code(ctx, group_name='foo'))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, "Grupo foo não existe")

    def test_group_exist_in_another_guild(self):
        ctx = FakeContext()
        guild2 = FakeGuild2()
        PromoCodeGroup.create(guild_id=guild2.id, name='foo')
        asyncio.run(list_code(ctx, group_name='foo'))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, "Grupo foo não existe")

    def test_group_does_not_have_codes(self):
        ctx = FakeContext()
        PromoCodeGroup.create(guild_id=ctx.guild.id, name='foo')
        asyncio.run(list_code(ctx, group_name='foo'))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, "Grupo foo não possui códigos")

    def test_group_has_codes(self):
        ctx = FakeContext()
        group = PromoCodeGroup.create(guild_id=ctx.guild.id, name='foo')
        PromoCode.create(group=group, code='ASDF-1234')
        asyncio.run(list_code(ctx, group_name='foo'))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, "Códigos para o grupo foo: \n- ASDF-1234")
