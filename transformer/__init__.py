from abc import ABCMeta, abstractmethod


class BaseTransformer(metaclass=ABCMeta):
    def __init__(self):
        pass

    @abstractmethod
    def transform(self):
        pass


class BaseMapperMixin:
    def transform_to_list(self, data):
        data = [] if data is None else data
        data = [data] if isinstance(data, dict) else data
        return data

    def get_value_from_dict(self, data, key, default=None):
        try:
            result = data
            tokens = key.split(".")
            for token in tokens:
                result = result.get(token, None)
                if result is None:
                    return default
            return result
        except Exception as error:
            raise error
