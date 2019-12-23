# noqa: F401
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, \
                                AsyncIOMotorCursor, AsyncIOMotorDatabase

client = AsyncIOMotorClient(host='10.8.0.1', connect=False)
db: AsyncIOMotorDatabase = client.test


from .field import Field, StringField, EmailField, RegexField, IntegerField, \
                   TypeField, FloatField
from .document import Document, DocumentInvalidError, DocumentNotFoundError
from .conf import setup_database
