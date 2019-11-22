from bson import ObjectId
import pymongo
import re
# from . import db

client = pymongo.MongoClient(host='10.8.0.1')
db: pymongo.database.Database = client.test


class Document:
    _id: ObjectId = None
    collection: str = None
    meta = None

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            field = object.__getattribute__(self, key)
            field.set_value(value)
        self.fields = tuple(kwargs.keys())

    def __getattribute__(self, name):
        attribute = object.__getattribute__(self, name)
        if isinstance(attribute, Field):
            return attribute.value
        return attribute

    def __setattr__(self, name, value):
        try:
            attribute = self.raw_attr(name)
        except AttributeError:
            attribute = None
        if attribute and isinstance(attribute, Field):
            return attribute.set_value(value)
        return object.__setattr__(self, name, value)

    def save(self):
        """Update or insert the current document to the database if needed
        then return the response from the database
        """
        if not self._id:
            response = self.cursor.insert_one(self.to_dict())
            self._id = response.inserted_id
            return response
        return self.cursor.update_one({'_id': self._id}, self.to_dict())

    def delete(self):
        if not self._id:
            return
        return self.cursor.delete_one({'_id': self._id})

    def find(self, match: dict = None, one=True):
        if match is None:
            match = {}
        if one:
            return self.cursor.find_one(match)
        return self.cursor.find(match)

    @property
    def cursor(self) -> pymongo.database.Collection:
        return db[self.collection]

    def to_dict(self) -> dict:
        return dict({k: getattr(self, k) for k in self.fields})

    def raw_attr(self, name):
        return object.__getattribute__(self, name)

    def is_valid(self) -> bool:
        for field_name in self.fields:
            field = object.__getattribute__(self, field_name)
            if not field.is_valid():
                return False
        return True


class Field:
    value = None

    def set_value(self, value):
        self.value = value


class StringField(Field):
    def __init__(self, maxlen=None):
        self.maxlen = maxlen

    def is_valid(self) -> bool:
        if not isinstance(self.value, str):
            return False
        if not self.maxlen:
            return True
        return len(self.value) <= self.maxlen


class EmailField(StringField):
    def is_valid(self) -> bool:
        if not super().is_valid():
            return False
        if not re.match(r'[\w]+@[\w]+', self.value):
            return False
        return True


class User(Document):
    collection = 'user'
    name = StringField(maxlen=255)
    email = EmailField(maxlen=512)
