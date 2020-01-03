from typing import List, Any
from .keywords import Eq, Neq, In, Nin, Gte, Lte, Gt, Lt, Exists, Regex
from .exceptions import DocumentNotFoundError
from .tools import dict_deep_update, merge_values


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
            filter_dict = self.dict_path(path, value)
            dict_deep_update(instance.query, filter_dict,
                             on_conflict=merge_values)
        return instance

    @staticmethod
    def read_dict_path(data: dict, path: List['str']):
        x = data
        for node in path:
            x = x[node]
        return x

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

    def __iter__(self, sort=None, **kwargs):
        if not self.model:
            raise MissingModelError
        if sort:
            kwargs['sort'] = self.sort_instruction(sort)
        for instance in self.model.find(filter=self.query, **kwargs):
            yield instance

    def count(self) -> int:
        if not self.model:
            raise MissingModelError
        return self.model.get_collection().count_documents(self.query)

    def all(self, **kwargs) -> List['Document']:
        return list(self.__iter__(**kwargs))

    def raw(self, limit=None, sort: List[str] = None, offset: int =None,
            **kwargs):
        if not self.model:
            raise MissingModelError
        cursor = self.model.find_raw(self.query, **kwargs)
        return self._get_cursor(cursor, sort, offset, limit)

    def raw_all(self, **kwargs):
        """This function is just a helper for `QuerySet.raw` to quickly view
        the data state in the database without any abstraction on Document
        """
        return list(self.raw(**kwargs))

    @classmethod
    def _get_cursor(cls, cursor,
                    sort: List[str]= None,
                    offset: int = None,
                    limit: int = None):
        """Aplly any sort/offset/limit to the given cursor and return the
        updated cursor.
        """
        if sort:
            cursor = cursor.sort(cls.sort_instruction(sort))
        if offset:
            cursor = cursor.skip(offset)
        if limit:
            cursor = cursor.limit(limit)
        return cursor

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
        dict_deep_update(instance.query, b.query, on_conflict=merge_values)
        if not instance.model and b.model:
            instance.model = b.model
        return instance

    def distinct(self, key: str, **kwargs) -> List[Any]:
        if not self.model:
            raise MissingModelError
        return self.model.get_collection().distinct(
            key=key, query=self.query, **kwargs)

    @staticmethod
    def sort_instruction(order: List[str]) -> List[tuple]:
        """Convert a list for format:
        ['name', '-age'] to:
        [('name': 1), ('age': -1)]
        """
        def generate_tuple(word) -> tuple:
            if word.startswith('-'):
                return (word[1:], -1)
            return (word, 1)

        return [generate_tuple(word) for word in order]
