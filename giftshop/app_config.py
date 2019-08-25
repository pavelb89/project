""" Application configuration """

# Flask configuration
# https://flask.palletsprojects.com/en/1.1.x/config/
SECRET_KEY = 'abc'
DEBUG = False

# Custom configuration
SQLALCHEMY_TRACK_MODIFICATIONS = False

# PostrgreSQL
DB_USER = 'postgres'
DB_PASSWORD = 'postgres'
DB_NAME = 'postgres'
DB_HOST = 'postgres'
DB_PORT = 5433
SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'


# For development
#DB_USER = 'user'
#DB_PASSWORD = 'yandexschool'
#DB_NAME = 'shopdb'
#DB_HOST = 'localhost'
#DB_PORT = 5432
#SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
