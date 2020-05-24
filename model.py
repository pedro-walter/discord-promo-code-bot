from peewee import Model, IntegerField, CharField

class AuthorizedUser(Model):
    guild_id = IntegerField()
    user_id = IntegerField()

    class Meta:
        indexes = (
            (('guild_id', 'user_id'), True),
        )

class PromoCodeGroup(Model):
    guild_id = IntegerField()
    name = CharField()

    class Meta:
        indexes = (
            (('guild_id', 'name'), True),
        )
