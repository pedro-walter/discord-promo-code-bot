import asyncio
from datetime import datetime
import logging

from main import add_code, add_code_bulk, remove_code, list_code, send_code, my_codes
from model import PromoCodeGroup, PromoCode
from constants import DATETIME_FORMAT, LOCAL_TIMEZONE

from .utils import DBTestCase, FakeContext, FakeGuild2, FakeUser

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

    def test_invalid_code(self):
        ctx = FakeContext()
        PromoCodeGroup.create(guild_id=ctx.guild.id, name='foo')
        asyncio.run(add_code(ctx, group_name='foo', code='ASDF$1234'))

        self.assertTrue(ctx.send_called)
        self.assertEqual(
            ctx.send_parameters,
            "Código inválido: o código deve ser apenas letras, números e traços (-)"
        )

    def test_code_already_registered(self):
        ctx = FakeContext()
        group = PromoCodeGroup.create(guild_id=ctx.guild.id, name='foo')
        PromoCode.create(group=group, code="ASDF-1234")
        asyncio.run(add_code(ctx, group_name='foo', code='ASDF-1234'))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, "Código ASDF-1234 já cadastrado no grupo foo")

class TestAddCodeBulk(DBTestCase):
    def test_group_does_not_exist(self):
        ctx = FakeContext()
        asyncio.run(add_code_bulk(ctx, group_name='foo', code_bulk='ASDF-1234 QWER-5678,ZXCV-9012'))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, "Grupo de códigos promocionais não encontrado: foo")

    def test_group_exists_in_this_guild(self):
        ctx = FakeContext()
        PromoCodeGroup.create(guild_id=ctx.guild.id, name='foo')
        asyncio.run(add_code_bulk(ctx, group_name='foo', code_bulk='ASDF-1234 QWER-5678,ZXCV-9012'))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, "Códigos adicionados ao grupo foo")

        promo_codes = PromoCode.select()
        resulting_codes = ['ASDF-1234', 'QWER-5678', 'ZXCV-9012']
        for (promo_code, resulting_code) in zip(promo_codes, resulting_codes):
            self.assertEqual(promo_code.code, resulting_code)

    def test_group_does_not_exist_in_this_guild(self):
        ctx = FakeContext()
        guild2 = FakeGuild2()
        PromoCodeGroup.create(guild_id=guild2.id, name='foo')
        asyncio.run(add_code_bulk(ctx, group_name='foo', code_bulk='ASDF-1234 QWER-5678,ZXCV-9012'))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, "Grupo de códigos promocionais não encontrado: foo")


class TestRemoveCode(DBTestCase):
    def test_code_group_does_not_exist(self):
        ctx = FakeContext()
        asyncio.run(remove_code(ctx, group_name='foo', code='ASDF-1234'))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, "Código ASDF-1234 não encontrado no grupo foo")

    def test_code_does_not_exist(self):
        ctx = FakeContext()
        PromoCodeGroup.create(guild_id=ctx.guild.id, name='foo')
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

        self.assertTrue(ctx.author.send_called)
        self.assertEqual(ctx.author.send_parameters, "Códigos para o grupo foo: \n- ASDF-1234")

    def test_group_has_sent_codes(self):
        ctx = FakeContext()
        user = FakeUser()
        group = PromoCodeGroup.create(guild_id=ctx.guild.id, name='foo')
        sent_at = datetime.now()
        promo_code = PromoCode.create(
            group=group,
            code='ASDF-1234',
            sent_to_name=user.name,
            sent_to_id=user.id,
            sent_at=sent_at
        )
        asyncio.run(list_code(ctx, group_name='foo'))

        self.assertTrue(ctx.author.send_called)
        self.assertEqual(
            ctx.author.send_parameters,
            "Códigos para o grupo foo: \n- {0} enviado para o usuário {1} em {2} (UTC)".format(
                promo_code.code,
                user.name,
                sent_at.astimezone(LOCAL_TIMEZONE).strftime(DATETIME_FORMAT)
            )
        )

class TestSendCode(DBTestCase):
    def test_group_does_not_exist(self):
        ctx = FakeContext()
        user = FakeUser()
        asyncio.run(send_code(ctx, group_name='foo', user=user))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, "Grupo foo não existe")

    def test_group_exist_in_another_guild(self):
        ctx = FakeContext()
        user = FakeUser()
        guild2 = FakeGuild2()
        PromoCodeGroup.create(guild_id=guild2.id, name='foo')
        asyncio.run(send_code(ctx, group_name='foo', user=user))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, "Grupo foo não existe")

    def test_group_has_code_and_user_has_already_received_one(self):
        ctx = FakeContext()
        user = FakeUser()
        group = PromoCodeGroup.create(guild_id=ctx.guild.id, name='foo')
        PromoCode.create(group=group, code='ASDF-1234', sent_to_id=user.id)
        asyncio.run(send_code(ctx, group_name='foo', user=user))

        self.assertTrue(ctx.send_called)
        self.assertEqual(
            ctx.send_parameters,
            "Usuário {0} já resgatou código do grupo {1}".format(user.name, 'foo')
        )

    def test_group_has_code_and_user_has_not_yet_received_one(self):
        ctx = FakeContext()
        user = FakeUser()
        group = PromoCodeGroup.create(guild_id=ctx.guild.id, name='foo')
        promo_code = PromoCode.create(group=group, code='ASDF-1234')
        asyncio.run(send_code(ctx, group_name='foo', user=user))

        self.assertTrue(ctx.author.send_called)
        self.assertEqual(
            ctx.author.send_parameters,
            "Código {} enviado para o usuário {}".format(promo_code.code, user.name)
        )

        self.assertTrue(user.send_called)
        self.assertEqual(
            user.send_parameters,
            "Olá! Você ganhou um código: {}".format(promo_code.code)
        )

        saved_promo_code = PromoCode.get(group=group, code=promo_code.code)

        self.assertEqual(saved_promo_code.sent_to_name, user.name)
        self.assertEqual(saved_promo_code.sent_to_id, user.id)
        self.assertIsNotNone(saved_promo_code.sent_at)

class TestMyCodes(DBTestCase):
    def test_user_has_no_codes(self):
        ctx = FakeContext()
        asyncio.run(my_codes(ctx))

        self.assertTrue(ctx.author.send_called)
        self.assertEqual(ctx.author.send_parameters, "Você não possui códigos")

    def test_user_has_codes(self):
        ctx = FakeContext()
        author = ctx.author
        sent_at = datetime.now()
        group = PromoCodeGroup.create(guild_id=ctx.guild.id, name='foo')
        promo_code = PromoCode.create(
            group=group,
            code='ASDF-1234',
            sent_to_id=author.id,
            sent_to_name=author.name,
            sent_at=sent_at
        )
        asyncio.run(my_codes(ctx))

        self.assertTrue(ctx.author.send_called)
        self.assertEqual(
            ctx.author.send_parameters,
            "Seus códigos: \n- {0} (recebido em {1})".format(
                promo_code.code,
                sent_at.astimezone(LOCAL_TIMEZONE).strftime(DATETIME_FORMAT)
            )
        )
