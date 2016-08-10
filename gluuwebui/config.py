import os


class Config(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = 'secret_key'
    API_SERVER_URL = os.environ.get(
        "API_SERVER_URL",
        "http://gluuengine:8080",
    )


class ProductionConfig(Config):
    SECRET_KEY = 'production_secret'


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
