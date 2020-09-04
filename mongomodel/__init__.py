# noqa: F401
import pymongo


class Database:
    def __init__(self):
        self.connect(host='localhost', connect=False)

    def connect(self, **kwargs) -> 'Database':
        kwargs.setdefault('connect', True)
        db_name = kwargs.pop('db', 'test')

        self.client = pymongo.MongoClient(**kwargs)
        self.db: pymongo.database.Database = getattr(self.client, db_name)
        return self

    def __repr__(self):
        return f'<Database: {self.client.HOST}: {self.db}>'

    def update_queryset(self, queryset):
        queryset._db = self

    def new(self, **kwargs) -> 'Database':
        return Database().connect()


database = Database()

from .field import (
    Field,
    StringField,
    EmailField,
    RegexField,
    IntegerField,
    TypeField,
    FloatField,
    DateTimeField,
    BoolField
)
from .document import Document, QuerySet  # noqa: F401
