import unittest

from peewee import SqliteDatabase

from constants import MODELS

class FakeUser():
    id = 123
    name = 'foo'


class FakeUser2():
    id = 321
    name = 'eggs'


class FakeGuild():
    id = 456
    name = 'bar'


class FakeGuild2():
    id = 789
    name = 'spam'


class FakeContext():
    send_called = False
    send_parameters = None
    def __init__(self, author=None, guild=None):
        self.author = FakeUser() if author is None else author
        self.guild = FakeGuild() if guild is None else guild

    async def send(self, params):
        self.send_called = True
        self.send_parameters = params


async def fake_fetch_user(user_id): # pylint: disable=unused-argument
    return FakeUser()


async def returns_true(*args): # pylint: disable=unused-argument
    return True


async def returns_false(*args): # pylint: disable=unused-argument
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
