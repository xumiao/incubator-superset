# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os

from flask_appbuilder.const import AUTH_OAUTH


def get_env_variable(var_name, default=None):
    """Get the environment variable or raise exception."""
    try:
        return os.environ[var_name]
    except KeyError:
        if default is not None:
            return default
        else:
            error_msg = 'The environment variable {} was missing, abort...'\
                        .format(var_name)
            raise EnvironmentError(error_msg)


POSTGRES_USER = get_env_variable('POSTGRES_USER')
POSTGRES_PASSWORD = get_env_variable('POSTGRES_PASSWORD')
POSTGRES_HOST = get_env_variable('POSTGRES_HOST')
POSTGRES_PORT = get_env_variable('POSTGRES_PORT')
POSTGRES_DB = get_env_variable('POSTGRES_DB')

# The SQLAlchemy connection string.
SQLALCHEMY_DATABASE_URI = 'postgresql://%s:%s@%s:%s/%s' % (POSTGRES_USER,
                                                           POSTGRES_PASSWORD,
                                                           POSTGRES_HOST,
                                                           POSTGRES_PORT,
                                                           POSTGRES_DB)
REDIS_HOST = get_env_variable('REDIS_HOST')
REDIS_PORT = get_env_variable('REDIS_PORT')

SECRET_KEY = '\2\1thisisarandomlygeneratedstupickeysforsupernorm'
FLASK_USE_RELOAD = True

LOG_FORMAT = '%(asctime)s:%(levelname)s:%(name)s:%(lineno)d:%(message)s'

DEBUG = False

SQLLAB_TIMEOUT = 30 * 60


class CeleryConfig(object):
    BROKER_URL = 'redis://%s:%s/0' % (REDIS_HOST, REDIS_PORT)
    CELERY_IMPORTS = ('superset.sql_lab', )
    CELERY_RESULT_BACKEND = 'redis://%s:%s/1' % (REDIS_HOST, REDIS_PORT)
    CELERY_ANNOTATIONS = {'tasks.add': {'rate_limit': '10/s'}}
    CELERY_TASK_PROTOCOL = 1


CELERY_CONFIG = CeleryConfig

CSRF_ENABLED = True

#AUTH_TYPE = AUTH_OAUTH
AUTH_USER_REGISTRATION = True
AUTH_USER_REGISTRATION_ROLE = "Public"
RECAPTCHA_USE_SSL = True
RECAPTCHA_PUBLIC_KEY = '6LfqG2cUAAAAAGvRGZnMC5-wNsITHuq1HjVLSlB7'
RECAPTCHA_PRIVATE_KEY = '6LfqG2cUAAAAAOPMCcOeXBVllXbsS0-cTGjzIdiH'
RECAPTCHA_OPTIONS = {'theme': 'white'}

#OAUTH_PROVIDERS = [{
#   'name': 'google',
#   'icon': 'fa-google',
#   'token_key': 'access_token',
#   'remote_app': {
#     'base_url': 'https://www.googleapis.com/oauth2/v2/',
#     'request_token_params': {
#        'scope': 'email profile'
#     },
#     'request_token_url': None,
#     'access_token_url': 'https://accounts.google.com/o/oauth2/token',
#     'authorize_url': 'https://accounts.google.com/o/oauth2/auth',
#     'consumer_key': '62152624246-89s61p6imb5l8e2adc50td88f9oni4o2.apps.googleusercontent.com',
#     'consumer_secret': 'gEOpH4jX8hjOjhhk1shRs6uj'
#    }
#}]

APP_NAME = 'SuperNorm'
APP_ICON = '/static/assets/images/supernorm-logo@2x.png'

DATA_STORAGE_ROOT = '/home/work/supernorm/data'


CACHE_DEFAULT_TIMEOUT = 60 * 60 * 24
CACHE_CONFIG = {'CACHE_TYPE': 'norm.cache.simple'}


