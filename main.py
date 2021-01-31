from datetime import datetime, timezone
import logging
import os

from discord import User
from discord.ext import commands
from dotenv import load_dotenv
from peewee import SqliteDatabase, IntegrityError

from constants import MODELS, DATETIME_FORMAT, LOCAL_TIMEZONE
from model import AuthorizedUser, PromoCodeGroup, PromoCode
from utils import (validate_group_name,
                   parse_codes_in_bulk,
                   validate_code,
                   sqlite_datetime_hack,
                   send_long_message_array)

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

bot = commands.Bot(command_prefix='$')

db = SqliteDatabase('database.sqlite', pragmas={'foreign_keys': 1})

db.bind(MODELS)
db.create_tables(MODELS)


@bot.event
async def on_ready():
    logging.info('Logged on as %s!', bot.user)


async def is_authorized_or_owner(ctx, is_owner=bot.is_owner):
    if await is_owner(ctx.author):
        return True
    user = AuthorizedUser.get_or_none(
        (AuthorizedUser.user_id == ctx.author.id)
        &
        (AuthorizedUser.guild_id == ctx.guild.id)
    )
    return user is not None


@bot.command()
@commands.check(is_authorized_or_owner)
async def echo(ctx, arg):
    await ctx.send(arg)


@bot.command()
@commands.check(is_authorized_or_owner)
async def echo_dm(ctx, arg):
    await ctx.author.send(arg)


# =======================================================
#               USER COMMANDS
# =======================================================
@bot.command()
@commands.is_owner()
async def add_user(ctx, *, user: User):
    """Adds a user to the authorized user list."""
    logging.info(
        "Estão tentando adicionar o usuário com ID %s aos usuários autorizados",  # noqa E501
        user.id)
    try:
        AuthorizedUser.create(guild_id=ctx.guild.id, user_id=user.id)
        await ctx.send("Adicionado usuário {}".format(user.name))
    except IntegrityError:
        await ctx.send("Usuário já autorizado")


@bot.command()
@commands.is_owner()
async def remove_user(ctx, *, user: User):
    """Removes a user from the authorized user list."""
    logging.info(
        "Estão tentando remover o usuário com ID %s dos usuários autorizados",
        user.id)
    query = AuthorizedUser.delete().where(
        (AuthorizedUser.user_id == user.id)
        &
        (AuthorizedUser.guild_id == ctx.guild.id)
    )
    rows_removed = query.execute()
    if rows_removed > 0:
        await ctx.send("Usuário {} desautorizado".format(user.name))
    else:
        await ctx.send("Usuário não estava autorizado: {}".format(user.name))


@bot.command()
@commands.is_owner()
async def list_user(ctx, fetch_user=bot.fetch_user):
    """Lists the authorized users."""
    logging.info("Estão tentando listar os usuários autorizados")
    authorized_users = AuthorizedUser.select().where(
        AuthorizedUser.guild_id == ctx.guild.id)
    if authorized_users.count() == 0:  # pylint: disable=no-value-for-parameter
        await ctx.send("Não há usuários autorizados")
        return
    output = "Estes são os usuários autorizados: "
    for authorized_user in authorized_users:
        discord_user = await fetch_user(authorized_user.user_id)
        output += "\n- {}".format(discord_user.name)
    await ctx.send(output)


# =======================================================
#               PROMO CODE GROUP COMMANDS
# =======================================================
@bot.command()
@commands.check(is_authorized_or_owner)
async def add_group(ctx, group_name):
    """Creates a group of promo codes.

    No code can live outside of a group (they get lonely!)."""
    logging.info("Tentando adicionar grupo '%s'", group_name)
    if not validate_group_name(group_name):
        await ctx.send(
            "Nome de grupo inválido. Use apenas letras, números, traços (-) e underscore (_)")  # noqa E501
        return
    try:
        PromoCodeGroup.create(guild_id=ctx.guild.id, name=group_name)
        await ctx.send("Grupo {} criado".format(group_name))
    except IntegrityError:
        await ctx.send("Grupo já existente")


@bot.command()
@commands.check(is_authorized_or_owner)
async def remove_group(ctx, group_name):
    """Destroys a promo code group.

    Careful! All codes within it are brutally killed too!"""
    logging.info("Tentando remover grupo '%s'", group_name)
    query = PromoCodeGroup.delete().where(
        (PromoCodeGroup.guild_id == ctx.guild.id)
        &
        (PromoCodeGroup.name == group_name)
    )
    rows_removed = query.execute()
    if rows_removed > 0:
        await ctx.send("Grupo {} removido".format(group_name))
    else:
        await ctx.send("Grupo {} não existe!".format(group_name))


@bot.command()
@commands.check(is_authorized_or_owner)
async def list_group(ctx):
    """Let's you see the promo code groups."""
    logging.info("Tentando listar grupos")
    groups = PromoCodeGroup.select().where(
        PromoCodeGroup.guild_id == ctx.guild.id)
    if groups.count() == 0:  # pylint: disable=no-value-for-parameter
        await ctx.send("Não há grupos de código promocional cadastrados")
        return
    output = "Estes são os grupos de código promocional existentes: "
    for group in groups:
        output += "\n- {}".format(group.name)
    await ctx.send(output)


# =======================================================
#               PROMO CODE COMMANDS
# =======================================================
@bot.command()
@commands.check(is_authorized_or_owner)
async def add_code(ctx, group_name, code):
    """Add a code to a promo group."""
    logging.info("Tentando adicionar o código %s ao grupo %s",
                 code,
                 group_name)
    if not validate_code(code):
        await ctx.send(
            "Código inválido: o código deve ser apenas letras, números e traços (-)")  # noqa E501
        return
    try:
        group = PromoCodeGroup.get(
            (PromoCodeGroup.guild_id == ctx.guild.id)
            &
            (PromoCodeGroup.name == group_name)
        )
        PromoCode.create(group=group, code=code)
        await ctx.send(
            "Código {0} cadastrado no grupo {1} com sucesso!".format(
                code,
                group_name))
    except PromoCodeGroup.DoesNotExist:  # pylint: disable=no-member
        await ctx.send(
            "Grupo de códigos promocionais não encontrado: {}".format(
                group_name))
    except IntegrityError:
        await ctx.send(
            "Código {0} já cadastrado no grupo {1}".format(code, group_name))


@bot.command()
@commands.check(is_authorized_or_owner)
async def add_code_bulk(ctx, group_name, *, code_bulk):
    """Adds a lot of codes to the same group.

    Codes are separated by anything that is not:
      - a letter
      - a number
      - a dash (-)"""
    logging.info("Tentando adicionar códigos em massa ao grupo %s: %s",
                 group_name,
                 code_bulk)
    group = PromoCodeGroup.get_or_none(
        (PromoCodeGroup.guild_id == ctx.guild.id)
        &
        (PromoCodeGroup.name == group_name)
    )
    if group is None:
        await ctx.send(
            "Grupo de códigos promocionais não encontrado: {}".format(
                group_name
            )
        )
        return
    codes = parse_codes_in_bulk(code_bulk)
    insert_bulk_data = [{'group': group, 'code': code} for code in codes]
    with db.atomic() as transaction:
        PromoCode.insert_many(insert_bulk_data).execute()  # noqa E501 pylint: disable=no-value-for-parameter
        transaction.commit()
    await ctx.send("Códigos adicionados ao grupo {}".format(group_name))


@bot.command()
@commands.check(is_authorized_or_owner)
async def remove_code(ctx, group_name, code):
    """Removes a code from a code group."""
    logging.info("Tentando remover o código %s do grupo %s", code, group_name)
    group = PromoCodeGroup.get_or_none(
        (PromoCodeGroup.guild_id == ctx.guild.id)
        &
        (PromoCodeGroup.name == group_name)
    )
    if group is None:
        await ctx.send(
            "Código {0} não encontrado no grupo {1}".format(code, group_name)
        )
        return
    query = PromoCode.delete().where(
        (PromoCode.code == code) & (PromoCode.group == group)
    )
    rows_removed = query.execute()
    if rows_removed > 0:
        await ctx.send(
            "Código {0} excluído do grupo {1}".format(code, group_name)
        )
    else:
        await ctx.send(
            "Código {0} não encontrado no grupo {1}".format(code, group_name)
        )


@bot.command()
@commands.check(is_authorized_or_owner)
async def list_code(ctx, group_name):
    """Lists all codes inside a code group."""
    logging.info("Tentando listar os códigos do grupo %s", group_name)
    group = PromoCodeGroup.get_or_none(
        (PromoCodeGroup.guild_id == ctx.guild.id)
        &
        (PromoCodeGroup.name == group_name)
    )
    if group is None:
        await ctx.send("Grupo {} não existe".format(group_name))
        return
    codes = PromoCode.select().where((PromoCode.group == group))
    if codes.count() == 0:  # pylint: disable=no-value-for-parameter
        await ctx.send("Grupo {} não possui códigos".format(group_name))
        return
    output = "Códigos para o grupo {}: ".format(group_name)
    for code in codes:
        output += "\n- {}".format(code.code)
        sent_at = sqlite_datetime_hack(code.sent_at)
        if code.sent_to_id:
            output += " enviado para o usuário {0} em {1}".format(
                code.sent_to_name,
                sent_at.astimezone(LOCAL_TIMEZONE).strftime(DATETIME_FORMAT)
            )
    await send_long_message_array(ctx.author.send, output)


@bot.command()
@commands.check(is_authorized_or_owner)
async def send_code(ctx,
                    group_name,
                    users: commands.Greedy[User],
                    is_authorized_or_owner=is_authorized_or_owner):
    """Sends a promo code from a code group to each of the mentioned users."""
    logging.info(
        "Tentando enviar um código do grupo %s para o(s) usuário(s) %s",
        group_name, ', '.join([f'{user.name}({user.id})' for user in users])
    )
    group = PromoCodeGroup.get_or_none(
        (PromoCodeGroup.guild_id == ctx.guild.id)
        &
        (PromoCodeGroup.name == group_name)
    )
    if group is None:
        await ctx.send("Grupo {} não existe".format(group_name))
        return
    messages_author = []
    messages_channel = []
    with db.atomic() as transaction:
        for user in users:
            if not await is_authorized_or_owner(ctx):
                used_codes = PromoCode.select().where(
                    (PromoCode.group == group)
                    &
                    (PromoCode.sent_to_id == user.id)
                )
                if used_codes.count() > 0:
                    messages_channel.append(
                        "Usuário {0} já resgatou código do grupo {1}".format(
                            user.name, group_name)
                        )
                    continue
            promo_code = PromoCode.select().where(
                (PromoCode.group == group) & (PromoCode.sent_to_id == None) # noqa E501 pylint: disable=singleton-comparison
            ).first()
            promo_code.sent_to_name = user.name
            promo_code.sent_to_id = user.id
            promo_code.sent_at = datetime.now(timezone.utc)
            promo_code.save()
            await user.send(
                "Olá! Você ganhou um código: {}".format(promo_code.code)
            )
            # incluir essa linha nos testes!
            messages_author.append(
                "Código {} enviado para o usuário {}".format(
                    promo_code.code, user.name
                )
            )
            messages_channel.append(
                "Enviado código do grupo {} para o usuário {}".format(
                    group_name, user.name
                )
            )
        await ctx.send("\n".join(messages_channel))
        await ctx.author.send("\n".join(messages_author))
        transaction.commit()


@bot.command()
async def my_codes(ctx):
    """List the codes you received from me!"""
    logging.info(
        "O usuário %s (ID %s) está tentando listar os próprios códigos",
        ctx.author.name, ctx.author.id
    )
    promo_codes = PromoCode.select().where(
        (PromoCode.sent_to_id == ctx.author.id)
    )
    if promo_codes.count() == 0:
        await ctx.author.send("Você não possui códigos")
        return
    output = "Seus códigos: "
    for promo_code in promo_codes:
        sent_at = sqlite_datetime_hack(promo_code.sent_at)
        output += "\n- {0} (recebido em {1})".format(
            promo_code.code,
            sent_at.astimezone(LOCAL_TIMEZONE).strftime(DATETIME_FORMAT)
        )
    await ctx.author.send(output)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    bot.run(BOT_TOKEN)
    logging.info('Disconnecting from DB...')
    db.close()
    logging.info("DB disconnected!")
