from datetime import datetime
import re

def validate_group_name(group_name):
    return re.match('^[a-zA-Z0-9-_]+$', group_name) is not None

def validate_code(code):
    return re.match('^[a-zA-Z0-9-]+$', code) is not None

def parse_codes_in_bulk(code_bulk):
    return re.split('[^\w-]+', code_bulk)

def sqlite_datetime_hack(datetime_or_str):
    if datetime_or_str.__class__ == str:
        return datetime.fromisoformat(datetime_or_str)
    return datetime_or_str
