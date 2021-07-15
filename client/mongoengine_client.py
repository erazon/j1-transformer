import mongoengine


def connect_to_mongodb(config):
    try:
        mongoengine.connect(
            config.MONGODB_DATABASE,
            host=config.MONGODB_HOST,
            port=config.MONGODB_PORT,
            username=config.MONGODB_USERNAME,
            password=config.MONGODB_PASSWORD,
            authentication_source=config.MONGODB_AUTH_DATABASE
        )
    except Exception as e:
        raise e


def disconnect_to_mongodb(config=None):
    try:
        mongoengine.disconnect()
    except Exception as error:
        raise error
