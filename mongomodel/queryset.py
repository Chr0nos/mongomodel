from typing import List, Any
from .keywords import Eq, Neq, In, Nin, Gte, Lte, Gt, Lt, Exists, Regex
from .exceptions import DocumentNotFoundError


class MissingModelError(Exception):
    pass


class TooManyResults(Exception):
    pass


class QuerySet:
    query = {}
    # must be a Model class, not an instance
    model = None
    keywords = {
        'eq': Eq,
        'neq': Neq,
        'in': In,
        'nin': Nin,
        'gte': Gte,
        'lte': Lte,
        'gt': Gt,
        'lt': Lt,
        'exists': Exists,
        'regex': Regex
    }

    def __init__(self, model=None):
        self.model = model

    def copy(self) -> 'QuerySet':
        instance = QuerySet(self.model)
        instance.query = self.query.copy()
        return instance

    def filter(self, **kwargs) -> 'QuerySet':
        return self._inner_filter(False, **kwargs)

    def exclude(self, **kwargs) -> 'QuerySet':
        return self._inner_filter(True, **kwargs)

    def _inner_filter(self, invert=False, **kwargs) -> 'QuerySet':
        instance = self.copy()
        for key, value in kwargs.items():
            path, value = self.apply_keywords(value, key.split('__'),
                                              invert=invert)
            try:
                self.insert_criteria(instance, path, value)
            except KeyError:
                new_query_argument = self.dict_path(path, value)
                instance.query.update(new_query_argument)
        return instance

    @staticmethod
    def read_dict_path(data: dict, path: List['str']):
        x = data
        for node in path:
            x = x[node]
        return x

    @classmethod
    def insert_criteria(cls, instance: 'QuerySet', path: List['str'], value):
        """Try to insert the new criteria in the `instance` query,
        if the path does not exists this method will raise a `KeyError`
        in case of an old occurence of a path in the query, the criteria will
        be transformed in a dict if possible and then updated with the new
        criteria
        """
        old_criteria = cls.read_dict_path(instance.query, path)
        if not isinstance(old_criteria, dict):
            old_criteria = {'$eq': old_criteria}
            # TODO : OPTIMIZE THIS !!!
            cls.read_dict_path(
                instance.query, path[0:-1])[path[-1]] = old_criteria
        # print('insert', old_criteria, value, 'to', path)
        old_criteria.update(value)
        # raise KeyError

    @staticmethod
    def dict_path(path: List[str], value: Any = None) -> dict:
        """Construct a dictionary from a path to hold the given value,
        example:
        d = QuerySet.dict_path(['a', 'b', 'c'], 42)
        d == {'a': {'b': {'c': 42}}}
        """
        out = {}
        node = out
        last_node = None
        last_key = None
        for k in path:
            node[k] = {}
            last_node = node
            node = node[k]
            last_key = k
        last_node[last_key] = value
        return out

    @classmethod
    def apply_keywords(cls, raw_value, path: List[str], invert=False):
        if invert and path[-1] not in cls.keywords:
            path.append('eq')

        for cmd in path:
            try:
                op = cls.keywords[cmd](raw_value)
                return path[0:-1], op.as_mongo_expression(invert)
            except KeyError:
                pass
        return path, raw_value

    def __iter__(self, **kwargs):
        if not self.model:
            raise MissingModelError
        for instance in self.model.find(filter=self.query, **kwargs):
            yield instance

    def count(self) -> int:
        if not self.model:
            raise MissingModelError
        return self.model.get_collection().count_documents(self.query)

    def all(self, **kwargs) -> List['Document']:
        return list(self.__iter__(**kwargs))

    def raw(self, **kwargs):
        if not self.model:
            raise MissingModelError
        return self.model.find_raw(self.query, **kwargs)

    def first(self, **kwargs):
        try:
            return next(self.__iter__(**kwargs))
        except StopIteration:
            return None

    def get(self, **kwargs):
        instance = self.filter(**kwargs) if kwargs else self
        search = list(self.model.find_raw(instance.query).limit(2))
        count = len(search)
        if count > 1:
            raise TooManyResults('too many items received')
        if count == 0:
            raise DocumentNotFoundError(instance.query)
        model_instance = self.model(**search[0])
        return model_instance

    def __add__(self, b: 'QuerySet') -> 'QuerySet':
        instance = self.copy()
        instance.query.update(b.query)
        if not instance.model and b.model:
            instance.model = b.model
        return instance

    def distinct(self, key: str, **kwargs) -> List[Any]:
        if not self.model:
            raise MissingModelError
        return self.model.get_collection().distinct(
            key=key, query=self.query, **kwargs)
