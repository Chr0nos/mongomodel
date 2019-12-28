from typing import List, Any
from .keywords import Eq, Neq, In, Nin, And, Nand, Or, Nor


class QuerySet:
    query = {}
    keywords = {
        'eq': Eq(),
        'neq': Neq(),
        'or': Or(),
        'nor': Nor(),
        'in': In(),
        'nin': Nin(),
        'and': And(),
        'nand': Nand()
    }

    def filter(self, **kwargs):
        for key, value in kwargs.items():
            args = key.split('__')
            args = self.apply_keywords(args)
            self.query.update(self.dict_path(args, value))
        return self

    def exclude(self, **kwargs):
        for key, value in kwargs.items():
            args = self.apply_keywords(key.split('__'), invert=True)
            self.query.update(self.dict_path(args, value))
        return self

    def dict_path(self, path: List[str], value: Any = None) -> dict:
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
        lst = []
        attr = 'command' if not invert else 'inverse'
        for path in args:
            for arg in path:
                try:
                    lst.append(getattr(cls.keywords[arg], attr))
                except KeyError:
                    lst.append(arg)
        return lst
