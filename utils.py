from datetime import datetime
import re


def validate_group_name(group_name):
    return re.match('^[a-zA-Z0-9-_]+$', group_name) is not None


def validate_code(code):
    return re.match('^[a-zA-Z0-9-]+$', code) is not None


def parse_codes_in_bulk(code_bulk):
    return re.split('[^\w-]+', code_bulk)  # noqa W605


def sqlite_datetime_hack(datetime_or_str):
    if datetime_or_str.__class__ == str:
        return datetime.fromisoformat(datetime_or_str)
    return datetime_or_str


async def send_long_message_array(send_function,
                                  message,
                                  split_character="\n",
                                  chunk_size=1990):
    """Splits a message using the split_character
    and sends them in chunks of chunk_size"""
    if len(message) < chunk_size:
        await send_function(message)
        return

    chunks = []
    current_chunk = ""

    for piece in message.split(split_character):
        if len(piece) > chunk_size:
            raise Exception("Message can't have pieces bigger than chunk_size")
        if (len(piece) + len(current_chunk)) > chunk_size:
            chunks.append(current_chunk)
            current_chunk = piece + "\n"
        else:
            current_chunk += piece + "\n"

    if len(current_chunk) > 0:
        chunks.append(current_chunk)

    total_pages = len(chunks)

    for i, chunk in enumerate(chunks):
        await send_function(f'{chunk}\nPage {i+1}/{total_pages}')
