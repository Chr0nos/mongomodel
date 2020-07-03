# noqa: F401
import pymongo

client = pymongo.MongoClient(host='localhost', connect=False)
db: pymongo.database.Database = client.test


from .field import Field, StringField, EmailField, RegexField, IntegerField, \
                   TypeField, FloatField, DateTimeField, BoolField
from .document import Document, QuerySet
from .conf import setup_database
