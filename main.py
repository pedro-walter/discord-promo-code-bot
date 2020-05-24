from configparser import ConfigParser
import logging

from discord import User
from discord.ext import commands
from peewee import SqliteDatabase, IntegrityError

from model import AuthorizedUser

CONFIG_FILE = 'config.ini'

config = ConfigParser()
config.read(CONFIG_FILE)

BOT_TOKEN = config.get('DEFAULT', 'BOT_TOKEN')

bot = commands.Bot(command_prefix='$')

db = SqliteDatabase('database.sqlite')

db.bind([AuthorizedUser])
db.create_tables([AuthorizedUser])

@bot.event
async def on_ready():
    logging.info('Logged on as {0}!'.format(bot.user))

async def is_authorized_or_owner(ctx, is_owner=bot.is_owner):
    is_owner = await is_owner(ctx.author)
    if is_owner:
        return True
    try:
        AuthorizedUser.get(AuthorizedUser.id == ctx.author.id)
        return True
    except AuthorizedUser.DoesNotExist: # pylint: disable=no-member
        return False
    

@bot.command()
@commands.check(is_authorized_or_owner)
async def echo(ctx, arg):
    await ctx.send(arg)

@bot.command()
@commands.is_owner()
async def add_user(ctx, *, user: User):
    logging.info("Estão tentando adicionar o usuário com ID {} aos usuários autorizados".format(user.id))
    try:
        AuthorizedUser.create(id=user.id)
        await ctx.send("Adicionado usuário {}".format(user.name))
    except IntegrityError:
        await ctx.send("Usuário já autorizado")

@bot.command()
@commands.is_owner()
async def remove_user(ctx, *, user: User):
    logging.info("Estão tentando remover o usuário com ID {} dos usuários autorizados".format(user.id))
    query = AuthorizedUser.delete().where(AuthorizedUser.id == user.id)
    rows_removed = query.execute()
    if rows_removed > 0:
        await ctx.send("Usuário {} desautorizado".format(user.name))
    else:
        await ctx.send("Usuário não estava autorizado: {}".format(user.name))

@bot.command()
@commands.is_owner()
async def list_user(ctx, fetch_user=bot.fetch_user):
    logging.info("Estão tentando listar os usuários autorizados")
    authorized_users = AuthorizedUser.select()
    if authorized_users.count() == 0: # pylint: disable=no-value-for-parameter
        await ctx.send("Não há usuários autorizados")
        return
    output = "Estes são os usuários autorizados: "
    for authorized_user in authorized_users:
        discord_user = await fetch_user(authorized_user.id)
        output += "\n- {}".format(discord_user.name)
    await ctx.send(output)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    bot.run(BOT_TOKEN)
    logging.info('Disconnecting from DB...')
    db.close()
    logging.info("DB disconnected!")