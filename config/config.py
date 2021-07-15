import os
from pathlib import Path

from dotenv import load_dotenv

ENV_FILE = ".env"
env_path = Path('.').absolute() / ENV_FILE
# print("ENV PATH: {}".format(env_path))
load_dotenv(dotenv_path=env_path, verbose=False)


class Config(object):
    SEND_EVENT_MESSAGE = (os.getenv("SEND_EVENT_MESSAGE", "True") == "True")

    MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "mongorun")
    MONGODB_HOST = os.getenv("MONGODB_HOST", "localhost")
    MONGODB_PORT = int(os.getenv("MONGODB_PORT", "27017"))
    MONGODB_USERNAME = os.getenv("MONGODB_USERNAME", "user")
    MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD", "password123")
    MONGODB_AUTH_DATABASE = os.getenv("MONGODB_AUTH_DATABASE", "mongorun")

    ENV = os.getenv("ENV", "development")
    APPLICATION_ROOT = os.getenv("APPLICATION_ROOT", "")
    TESTING = (os.getenv("TESTING", "False") == "True")
    DEBUG = (os.getenv("DEBUG", "False") == "True")
    SECRET_KEY = os.getenv("SECRET_KEY", "secret")

    # print("<----- MongoConfig(Config) ----->\n"
    #       "database: {}\n"
    #       "host: {}\n"
    #       "port: {}\n"
    #       "user: {}\n"
    #       "password: {}\n"
    #       "MONGODB_AUTH_DATABASE: {}".format(
    #     MONGODB_DATABASE, MONGODB_HOST, MONGODB_PORT,
    #     MONGODB_USERNAME, MONGODB_PASSWORD,
    #     MONGODB_AUTH_DATABASE
    # ))
    # print("-" * 40)
