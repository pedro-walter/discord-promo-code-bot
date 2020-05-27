import pytz

from model import AuthorizedUser, PromoCodeGroup, PromoCode

CONFIG_FILE = 'config.ini'
DATETIME_FORMAT = '%d/%m/%Y %H:%M'
LOCAL_TIMEZONE = pytz.timezone('America/Sao_Paulo')
MODELS = [AuthorizedUser, PromoCodeGroup, PromoCode]
