import os
import django


ALLOWED_HOSTS = ["*"]


DB = {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": os.getenv("POSTGRES_DB"),
    "USER": os.getenv("POSTGRES_USER"),
    "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
    "HOST": "postgres",
    "PORT": 5432,
    "CONN_MAX_AGE": 300,
}

if django.VERSION > (5, 2):
    DATABASES = {"default": DB}
else:
    DATABASE = DB


REDIS = {
    "tasks": {
        "HOST": "redis",
        "PORT": 6379,
        "USERNAME": "",
        "PASSWORD": os.getenv("REDIS_PASSWORD"),
        "DATABASE": 0,
        "SSL": False,
    },
    "caching": {
        "HOST": "redis",
        "PORT": 6379,
        "USERNAME": "",
        "PASSWORD": os.getenv("REDIS_PASSWORD"),
        "DATABASE": 1,
        "SSL": False,
    },
}

ALLOW_TOKEN_RETRIEVAL = True

DEBUG = True

DEVELOPER = True

SECRET_KEY = os.getenv("SECRET_KEY")

ENABLE_LOCALIZATION = False
AUTH_PASSWORD_VALIDATORS = []
BASE_PATH = ''
CORS_ORIGIN_ALLOW_ALL = False
CORS_ORIGIN_WHITELIST = [
    # 'https://hostname.example.com',
]
CORS_ORIGIN_REGEX_WHITELIST = [
    # r'^(https?://)?(\w+\.)?example\.com$',
]

# The name to use for the CSRF token cookie.
CSRF_COOKIE_NAME = 'csrftoken'
DEFAULT_LANGUAGE = 'en-us'
EMAIL = {
    'SERVER': 'localhost',
    'PORT': 25,
    'USERNAME': '',
    'PASSWORD': '',
    'USE_SSL': False,
    'USE_TLS': False,
    'TIMEOUT': 10,  # seconds
    'FROM_EMAIL': '',
}
EXEMPT_VIEW_PERMISSIONS = []
LOGIN_PERSISTENCE = False
LOGIN_REQUIRED = True
LOGIN_TIMEOUT = None
LOGOUT_REDIRECT_URL = 'home'
METRICS_ENABLED = False
REMOTE_AUTH_ENABLED = False
REMOTE_AUTH_BACKEND = 'netbox.authentication.RemoteUserBackend'
REMOTE_AUTH_HEADER = 'HTTP_REMOTE_USER'
REMOTE_AUTH_USER_FIRST_NAME = 'HTTP_REMOTE_USER_FIRST_NAME'
REMOTE_AUTH_USER_LAST_NAME = 'HTTP_REMOTE_USER_LAST_NAME'
REMOTE_AUTH_USER_EMAIL = 'HTTP_REMOTE_USER_EMAIL'
REMOTE_AUTH_AUTO_CREATE_USER = True
REMOTE_AUTH_DEFAULT_GROUPS = []
REMOTE_AUTH_DEFAULT_PERMISSIONS = {}
RELEASE_CHECK_URL = None
RQ_DEFAULT_TIMEOUT = 300
SESSION_COOKIE_NAME = 'sessionid'
SESSION_FILE_PATH = None
TIME_ZONE = 'UTC'

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "timestamp": {
            "format": "{asctime} [{levelname}] {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "timestamp"},
    },
    "loggers": {"validity": {"handlers": ["console"], "level": "INFO"}},
}


PLUGINS = ["validity"]
PLUGINS_CONFIG = {"validity": {}}


# for debug toolbar
class ContainsAll:
    def __contains__(self, v):
        return True


INTERNAL_IPS = ContainsAll()


CUSTOM_VALIDATORS = {"core.datasource": ["validity.custom_validators.DataSourceValidator"]}
