import asyncio
import logging
import unittest

from peewee import SqliteDatabase

from main import echo, add_user, remove_user, list_user, is_authorized_or_owner
from model import AuthorizedUser

logging.basicConfig(level=logging.ERROR)

MODELS = [AuthorizedUser]


#=======================================================
#               UTILITY CLASSES AND FUNCTIONS
#=======================================================
class FakeUser():
    id = 123
    name = 'foo'


class FakeContext():
    send_called = False
    send_parameters = None
    def __init__(self):
        self.author = FakeUser()

    async def send(self, params):
        self.send_called = True
        self.send_parameters = params


async def fake_fetch_user(user_id):
    return FakeUser()


async def returns_true(*args):
    return True


async def returns_false(*args):
    return False


class DBTestCase(unittest.TestCase):
    def setUp(self):
        # use an in-memory SQLite for tests.
        self.test_db = SqliteDatabase(':memory:')

        # Bind model classes to test db. Since we have a complete list of
        # all models, we do not need to recursively bind dependencies.
        self.test_db.bind(MODELS, bind_refs=False, bind_backrefs=False)

        self.test_db.connect()
        self.test_db.create_tables(MODELS)

    def tearDown(self):
        # Not strictly necessary since SQLite in-memory databases only live
        # for the duration of the connection, and in the next step we close
        # the connection...but a good practice all the same.
        self.test_db.drop_tables(MODELS)

        # Close connection to db.
        self.test_db.close()

        # If we wanted, we could re-bind the models to their original
        # database here. But for tests this is probably not necessary.


class TestUtilityClasses(unittest.TestCase):
    def test_fake_ctx(self):
        ctx = FakeContext()
        self.assertFalse(ctx.send_called)
        self.assertIsNone(ctx.send_parameters)

        asyncio.run(ctx.send('foo'))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, 'foo')


#=======================================================
#               TEST CASES
#=======================================================
class TestEcho(unittest.TestCase):
    def test_echo(self):
        ctx = FakeContext()
        asyncio.run(echo(ctx, 'foo'))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, 'foo')


class TestAddUser(DBTestCase):
    def test_add_user(self):
        ctx = FakeContext()
        user = FakeUser()
        asyncio.run(add_user(ctx, user=user))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, "Adicionado usuário foo")

        authorized_user = AuthorizedUser.get(AuthorizedUser.id == user.id)

        self.assertEqual(authorized_user.id, user.id)

        ctx = FakeContext()
        asyncio.run(add_user(ctx, user=user))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, "Usuário já autorizado")


class TestRemoveUser(DBTestCase):
    def test_user_exists(self):
        user = FakeUser()
        AuthorizedUser.create(id=user.id)

        ctx = FakeContext()
        asyncio.run(remove_user(ctx, user=user))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, "Usuário {} desautorizado".format(user.name))

    def test_user_does_not_exist(self):
        user = FakeUser()
        ctx = FakeContext()
        asyncio.run(remove_user(ctx, user=user))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, "Usuário não estava autorizado: {}".format(user.name))


class TestListUser(DBTestCase):
    def test_has_no_results(self):
        ctx = FakeContext()
        asyncio.run(list_user(ctx, fetch_user=fake_fetch_user))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, "Não há usuários autorizados")

    def test_has_results(self):
        user = FakeUser()
        AuthorizedUser.create(id=user.id)

        ctx = FakeContext()
        asyncio.run(list_user(ctx, fetch_user=fake_fetch_user))

        self.assertTrue(ctx.send_called)
        self.assertEqual(ctx.send_parameters, "Estes são os usuários autorizados: \n- {}".format(user.name))


class TestIsAuthorizedOrOwner(DBTestCase):
    def test_owner_is_authorized(self):
        ctx = FakeContext()
        result = asyncio.run(is_authorized_or_owner(ctx, is_owner=returns_true))
        self.assertTrue(result)

    
    def test_user_is_authorized(self):
        ctx = FakeContext()
        AuthorizedUser.create(id=ctx.author.id)
        result = asyncio.run(is_authorized_or_owner(ctx, is_owner=returns_false))
        self.assertTrue(result)


    def test_user_is_not_authorized(self):
        ctx = FakeContext()
        result = asyncio.run(is_authorized_or_owner(ctx, is_owner=returns_false))
        self.assertFalse(result)



if __name__ == '__main__':
    unittest.main()