from peewee import SqliteDatabase, Model, IntegerField

class AuthorizedUser(Model):
    id = IntegerField(primary_key=True)