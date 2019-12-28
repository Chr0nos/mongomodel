from typing import List, Any
from .keywords import Eq, Neq, In, Nin, And, Nand, Or, Nor, Gte, Lte, Gt, Lt
from .exceptions import DocumentNotFoundError


class MissingModelError(Exception):
    pass


class TooManyResults(Exception):
    pass


class QuerySet:
    query = {}
    model = None
    keywords = {
        'eq': Eq(),
        'neq': Neq(),
        'or': Or(),
        'nor': Nor(),
        'in': In(),
        'nin': Nin(),
        'and': And(),
        'nand': Nand(),
        'gte': Gte(),
        'lte': Lte(),
        'gt': Gt(),
        'lt': Lt()
    }

    def __init__(self, model=None):
        self.model = model

    def copy(self) -> 'QuerySet':
        instance = QuerySet(self.model)
        instance.query = self.query.copy()
        return instance

    def filter(self, **kwargs) -> 'QuerySet':
        instance = self.copy()
        for key, value in kwargs.items():
            args = key.split('__')
            args = self.apply_keywords(args)
            instance.query.update(self.dict_path(args, value))
        return instance

    def exclude(self, **kwargs) -> 'QuerySet':
        instance = self.copy()
        for key, value in kwargs.items():
            args = self.apply_keywords(key.split('__'), invert=True)
            instance.query.update(self.dict_path(args, value))
        return instance

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
    def apply_keywords(cls, *args, invert=False) -> List[str]:
        attr = 'command' if not invert else 'inverse'

        def apply_arg(arg):
            try:
                return getattr(cls.keywords[arg], attr)
            except KeyError:
                return arg

        def apply_path(path: List[str]):
            # explicitly set final equality argument.
            if invert and path[-1] not in cls.keywords:
                path.append('eq')
            return [apply_arg(arg) for arg in path]

        lst = []
        for path in args:
            lst.extend(apply_path(path))
        return lst

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
        return next(self.__iter__(**kwargs))

    def get(self, **kwargs):
        instance = self.filter(**kwargs) if kwargs else self
        count = instance.count()
        if count > 1:
            raise TooManyResults(f'too many items received: {count}')
        if count == 0:
            raise DocumentNotFoundError(instance.query)
        return instance.first()

    def __add__(self, b: 'QuerySet') -> 'QuerySet':
        instance = self.copy()
        instance.query.update(b.query)
        if not instance.model and b.model:
            instance.model = b.model
        return instance
