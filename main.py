from configparser import ConfigParser
import logging

from discord import User
from discord.ext import commands
from peewee import SqliteDatabase, IntegrityError

from constants import CONFIG_FILE, MODELS
from model import AuthorizedUser, PromoCodeGroup
from utils import validate_group_name

config = ConfigParser()
config.read(CONFIG_FILE)

BOT_TOKEN = config.get('DEFAULT', 'BOT_TOKEN')

bot = commands.Bot(command_prefix='$')

db = SqliteDatabase('database.sqlite')

db.bind(MODELS)
db.create_tables(MODELS)

@bot.event
async def on_ready():
    logging.info('Logged on as %s!', bot.user)

async def is_authorized_or_owner(ctx, is_owner=bot.is_owner):
    is_owner = await is_owner(ctx.author)
    if is_owner:
        return True
    try:
        AuthorizedUser.get(
            (AuthorizedUser.user_id == ctx.author.id) & (AuthorizedUser.guild_id == ctx.guild.id)
        )
        return True
    except AuthorizedUser.DoesNotExist: # pylint: disable=no-member
        return False


@bot.command()
@commands.check(is_authorized_or_owner)
async def echo(ctx, arg):
    await ctx.send(arg)


#=======================================================
#               USER COMMANDS
#=======================================================
@bot.command()
@commands.is_owner()
async def add_user(ctx, *, user: User):
    logging.info("Estão tentando adicionar o usuário com ID %s aos usuários autorizados", user.id)
    try:
        AuthorizedUser.create(guild_id=ctx.guild.id, user_id=user.id)
        await ctx.send("Adicionado usuário {}".format(user.name))
    except IntegrityError:
        await ctx.send("Usuário já autorizado")

@bot.command()
@commands.is_owner()
async def remove_user(ctx, *, user: User):
    logging.info("Estão tentando remover o usuário com ID %s dos usuários autorizados", user.id)
    query = AuthorizedUser.delete().where(
        (AuthorizedUser.user_id == user.id) & (AuthorizedUser.guild_id == ctx.guild.id)
    )
    rows_removed = query.execute()
    if rows_removed > 0:
        await ctx.send("Usuário {} desautorizado".format(user.name))
    else:
        await ctx.send("Usuário não estava autorizado: {}".format(user.name))

@bot.command()
@commands.is_owner()
async def list_user(ctx, fetch_user=bot.fetch_user):
    logging.info("Estão tentando listar os usuários autorizados")
    authorized_users = AuthorizedUser.select().where(AuthorizedUser.guild_id == ctx.guild.id)
    if authorized_users.count() == 0: # pylint: disable=no-value-for-parameter
        await ctx.send("Não há usuários autorizados")
        return
    output = "Estes são os usuários autorizados: "
    for authorized_user in authorized_users:
        discord_user = await fetch_user(authorized_user.user_id)
        output += "\n- {}".format(discord_user.name)
    await ctx.send(output)

#=======================================================
#               PROMO CODE GROUP COMMANDS
#=======================================================
@bot.command()
@commands.check(is_authorized_or_owner)
async def add_group(ctx, group_name):
    logging.info("Tentando adicionar grupo '%s'", group_name)
    if not validate_group_name(group_name):
        await ctx.send(
            "Nome de grupo inválido. Use apenas letras, números, traços (-) e underscore (_)")
    try:
        PromoCodeGroup.create(guild_id=ctx.guild.id, name=group_name)
        await ctx.send("Grupo {} criado".format(group_name))
    except IntegrityError:
        await ctx.send("Grupo já existente")

@bot.command()
@commands.check(is_authorized_or_owner)
async def remove_group(ctx, group_name):
    logging.info("Tentando remover grupo '%s'", group_name)
    query = PromoCodeGroup.delete().where(
        (PromoCodeGroup.guild_id == ctx.guild.id) & (PromoCodeGroup.name == group_name)
    )
    rows_removed = query.execute()
    if rows_removed > 0:
        await ctx.send("Grupo {} removido".format(group_name))
    else:
        await ctx.send("Grupo {} não existe!".format(group_name))

@bot.command()
@commands.check(is_authorized_or_owner)
async def list_group(ctx):
    logging.info("Tentando listar grupos")
    groups = PromoCodeGroup.select().where(PromoCodeGroup.guild_id == ctx.guild.id)
    if groups.count() == 0: # pylint: disable=no-value-for-parameter
        await  ctx.send("Não há grupos de código promocional cadastrados")
        return
    output = "Estes são os grupos de código promocional existentes: "
    for group in groups:
        output += "\n- {}".format(group.name)
    await ctx.send(output)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    bot.run(BOT_TOKEN)
    logging.info('Disconnecting from DB...')
    db.close()
    logging.info("DB disconnected!")
