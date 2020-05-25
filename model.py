from peewee import Model, IntegerField, CharField, ForeignKeyField, DateTimeField

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
    sent_to_name = CharField(null=True)
    sent_to_id = IntegerField(null=True, index=True)
    sent_at = DateTimeField(null=True)

    class Meta:
        indexes = (
            (('group_id', 'code'), True),
            (('group_id', 'sent_to_id'), True),
        )
