# noqa: F401
import pymongo

client = pymongo.MongoClient(host='10.8.0.1', connect=False)
db: pymongo.database.Database = client.test


from .field import Field, StringField, EmailField, RegexField, IntegerField, \
                   TypeField, FloatField, DateTimeField, BoolField
from .document import Document, QuerySet
from .conf import setup_database
