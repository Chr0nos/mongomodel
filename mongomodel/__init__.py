# noqa: F401
import pymongo

client = pymongo.MongoClient(host='10.8.0.1', connect=False)
db: pymongo.database.Database = client.test


from .field import Field, StringField, EmailField, RegexField, IntegerField, \
                   TypeField, FloatField
from .document import Document, DocumentInvalidError, DocumentNotFoundError
from .conf import setup_database
