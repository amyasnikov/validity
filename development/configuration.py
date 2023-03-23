import os
import socket

from .configuration_example import *


ALLOWED_HOSTS = ['*']

DATABASE = {
    "NAME": os.getenv("POSTGRES_DB"),
    "USER": os.getenv("POSTGRES_USER"),
    "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
    "HOST": "postgres",
    "PORT": 5432,
    "CONN_MAX_AGE": 300,
}


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

DEBUG = True

DEVELOPER = True

SECRET_KEY = os.getenv("SECRET_KEY")

ENABLE_LOCALIZATION = False


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'timestamp': {
            'format': '{asctime} [{levelname}] {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'timestamp'},
    },
    'loggers': {
        'validity': {'handlers': ['console'], 'level': 'INFO'}
    },
}

PLUGINS.append("validity")

PLUGINS_CONFIG = {
    "validity": {
        "store_last_results": 5,
        "git_folder": "/opt/git_repos/",
        "autocopy_scripts": True
    }
}

# for debug toolbar
_, _, _ips = socket.gethostbyname_ex(socket.gethostname())
INTERNAL_IPS += tuple(ip[: ip.rfind(".")] + ".1" for ip in _ips)
