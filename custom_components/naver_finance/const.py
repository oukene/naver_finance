import voluptuous as vol
import homeassistant.helpers.config_validation as cv

# This is the internal name of the integration, it should also match the directory
# name for the integration.
DOMAIN = "naver_finance"
NAME = "Naver Finance"
VERSION = "1.0.0"

CONF_OPTION_MODIFY = "option_modify"
CONF_OPTION_ADD = "option_add"
CONF_OPTION_SELECT = "option_select"
CONF_OPTION_DELETE = "option_delete"
CONF_OPTION_ENTITIES = "option_entities"

CONF_OPTIONS = [
    CONF_OPTION_MODIFY,
    CONF_OPTION_ADD
]

CURRENCY_TYPES = [
    "원",
    "KRW",
    "달러",
    "USD",
]

CONF_KEYWORDS = "keywords"
CONF_WORD = "word"
CONF_REFRESH_PERIOD = "refresh_period"
CONF_UNIT = "unit"
CONF_IMAGE = "image"

CONF_URL = "https://search.naver.com/search.naver?&query="

REFRESH_MIN = 60
