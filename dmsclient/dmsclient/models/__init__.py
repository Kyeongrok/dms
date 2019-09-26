import abc
from enum import Enum


class BaseModel(abc.ABC):
    """
    Base class for DMS models (drive, segment, etc.).
    """

    def __init__(self, *args, **kwargs):
        self.extra_fields = kwargs

    @property
    @abc.abstractmethod
    def id(self):
        pass

    @property
    @abc.abstractmethod
    def timebased(self):
        pass

    @classmethod
    def from_elasticsearch(cls, document):
        """
        Create a model object from the Elasticsearch document returned by the
        `elasticsearch` module.

        :param document: the Elasticsearch document
        :type document: dict
        :return: a model object
        """
        return cls(**document['_source'])

    def to_dict(self):
        """
        Return the model object as a dict, ready to be created or updated on
        Elasticsearch.

        :return: the model dict
        :rtype: dict
        """
        def normalize(value):
            if isinstance(value, Enum):
                return value.value
            return value

        s = self.extra_fields.copy() if hasattr(self, 'extra_fields') else {}
        s.update(self.__dict__)
        s.pop('extra_fields', None)
        s = {k: normalize(v) for k, v in s.items()}
        return s

    def __eq__(self, other):
        return self.to_dict() == other.to_dict()

    def __str__(self):
        return "%s(ID='%s')" % (self.__class__.__name__, self.id)


class StrEnum(str, Enum):
    def __eq__(self, other):
        if self.__class__ is other.__class__:
            return other.value == self.value
        elif isinstance(other, str):
            return other == self.value
        else:
            return False
