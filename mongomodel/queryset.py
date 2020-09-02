from typing import List, Any
from .keywords import Eq, Neq, In, Nin, Gte, Lte, Gt, Lt, Exists, Regex
from .tools import dict_deep_update, merge_values
from . import database
from pymongo.collection import Collection
from pymongo.cursor import Cursor


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
    _sort = None
    _skip = None
    _limit = None
    _db = database

    def __init__(self, model=None, database=None):
        self.model = model
        if database:
            self._db = database

    def __str__(self):
        return f'{self.query}'

    def __repr__(self):
        return f'<QuerySet: {self}>'

    def copy(self) -> 'QuerySet':
        instance = QuerySet(self.model)
        instance.query = self.query.copy()
        instance._sort = self._sort
        instance._skip = self._skip
        instance._limit = self._limit
        instance._db = self._db
        return instance

    def sort(self, order):
        instance = self.copy()
        instance._sort = self.sort_instruction(order) if order else None
        return instance

    def skip(self, n: int):
        instance = self.copy()
        instance._skip = n
        return instance

    def limit(self, n: int):
        instance = self.copy()
        instance._limit = n
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

    def __iter__(self, **kwargs):
        if not self.model:
            raise MissingModelError
        if self._sort:
            kwargs['sort'] = self._sort
        if self._skip:
            kwargs['offset'] = self._skip
        if self._limit:
            kwargs['limit'] = self._limit
        for instance in self.find(filter=self.query, **kwargs):
            yield instance

    def count(self) -> int:
        if not self.model:
            raise MissingModelError
        return self.get_collection().count_documents(self.query)

    def all(self, **kwargs) -> List['Document']:
        return list(self.__iter__(**kwargs))

    def raw(self, **kwargs):
        if not self.model:
            raise MissingModelError
        cursor = self.find_raw(self.query, **kwargs)
        return self._get_cursor(cursor)

    def raw_all(self, **kwargs):
        """This function is just a helper for `QuerySet.raw` to quickly view
        the data state in the database without any abstraction on Document
        """
        return list(self.raw(**kwargs))

    def _get_cursor(self, cursor):
        """Aplly any sort/offset/limit to the given cursor and return the
        updated cursor.
        """
        if self._sort:
            cursor = cursor.sort(self._sort)
        if self._skip:
            cursor = cursor.skip(self._skip)
        if self._limit:
            cursor = cursor.limit(self._limit)
        return cursor

    def first(self, **kwargs):
        try:
            return next(self.__iter__(**kwargs))
        except StopIteration:
            return None

    def find_one(self, **kwargs):
        if self._sort:
            kwargs['sort'] = self._sort
        if self._skip:
            kwargs['offset'] = self._skip
        if self._limit:
            kwargs['limit'] = self._limit
        return self.get_collection().find_one(self.query, **kwargs)

    def get(self, **kwargs):
        instance = self.filter(**kwargs) if kwargs else self
        search = list(self.find_raw(instance.query).limit(2))
        count = len(search)
        if count > 1:
            raise TooManyResults('too many items received')
        if count == 0:
            # raise DocumentNotFoundError(instance.query)
            raise self.model.DoesNotExist(instance.query)
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
        return self.get_collection().distinct(
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

    def delete(self):
        if not self.model:
            raise MissingModelError
        collection = self.get_collection()
        cursor = self._get_cursor(collection.find(self.query))
        ids = cursor.distinct('_id')
        return collection.delete_many({'_id': {'$in': ids}})

    def get_collection_name(self) -> str:
        try:
            collection_name = self.model.collection
        except AttributeError:
            pass

        if not collection_name:
            collection_name = self.model.__name__.lower()
        return collection_name

    def get_collection(self) -> Collection:
        return self._db.db[self.get_collection_name()]

    def drop(self):
        return self.get_collection().drop()

    def find_raw(self, search: dict = None) -> Cursor:
        """Peforms a search in the database in raw mode: no Document will be
        created, all fields will be visible, use this for debugging purposes.
        """
        return self.get_collection().find(search if search else {})

    def find(self, filter: dict = None, **kwargs) -> List['Document']:
        cursor = self.get_collection().find(filter=filter, **kwargs)
        return [self.model(**item) for item in self._get_cursor(cursor)]
