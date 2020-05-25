from peewee import Model, IntegerField, CharField, ForeignKeyField

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

class PromoCode(Model):
    group = ForeignKeyField(PromoCodeGroup, backref='codes')
    code = CharField()

    class Meta:
        indexes = (
            (('group_id', 'code'), True),
        )
