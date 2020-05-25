import re

def validate_group_name(group_name):
    return re.match('^[a-zA-Z0-9-_]+$', group_name) is not None

def parse_codes_in_bulk(code_bulk):
    return re.split('[^\w-]+', code_bulk)
