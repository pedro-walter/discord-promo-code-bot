from peewee import SqliteDatabase, Model, IntegerField

class AuthorizedUser(Model):
    guild_id = IntegerField()
    user_id = IntegerField()

    class Meta:
        indexes = (
            (('guild_id', 'user_id'), True),
        )