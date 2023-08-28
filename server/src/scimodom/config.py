class Config(object):
    TESTING = False

class DevConfig(Config):
    DATABASE_URI = "mysql+mysqldb://eboileau:@localhost/scimodom"

class TestConfig(Config):
    DATABASE_URI = 'sqlite:///:memory:'
    TESTING = True
