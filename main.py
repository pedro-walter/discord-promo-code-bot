from configparser import ConfigParser

from discord import User
from discord.ext import commands

CONFIG_FILE = 'config.ini'

config = ConfigParser()
config.read(CONFIG_FILE)

BOT_TOKEN = config.get('DEFAULT', 'BOT_TOKEN')

bot = commands.Bot(command_prefix='$')

@bot.event
async def on_ready():
    print('Logged on as {0}!'.format(bot.user))

@bot.command()
@commands.is_owner()
async def echo(ctx, arg):
    await ctx.send(arg)

@bot.command()
async def add_user(ctx, *, user: User):
    print("Estão tentando adicionar o usuário com ID {} aos usuários autorizados".format(user.id))
    await ctx.send("Adicionando usuário {}".format(user.name))

bot.run(BOT_TOKEN)