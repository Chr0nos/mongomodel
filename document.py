from bson import ObjectId
import pymongo
import re
from . import db


class Document:
    _id: ObjectId = None
    collection: str = None
    meta = None

    def __init__(self, **kwargs):
        # TODO : remove this fuckery
        for key, value in kwargs:
            setattr(self, key, value)
        self.meta = kwargs.keys()

    def save(self):
        """Update or insert the current document to the database if needed
        then return the response from the database
        """
        if not self.id:
            response = self.cursor.insert_one(self.to_dict())
            self._id = response.inserted_id
            return response
        return self.cursor.update_one({'_id': self.id}, self.to_dict())

    def delete(self):
        if not self._id:
            return
        return self.cursor.delete_one({'_id': self._id})

    def find(self, match: dict, one=True):
        if one:
            return self.cursor.find_one(match)
        return self.cursor.find(match)

    @property
    def cursor(self) -> pymongo.database.Collection:
        return db[self.collection]

    def to_dict(self) -> dict:
        raise NotImplementedError


class Field:
    def __init__(self, data):
        self.data = data


class StringField(Field):
    def __init__(self, data, maxlen=None):
        super().__init__(data)
        self.maxlen = maxlen

    def is_valid(self) -> bool:
        if not isinstance(self.data, str):
            return False
        if not self.maxlen:
            return True
        return len(self.data) <= self.maxlen


class EmailField(StringField):
    def is_valid(self) -> bool:
        if not super().is_valid(self.data):
            return False
        if not re.match(r'[\w]+@[\w]+', self.data):
            return False
        return True


class User(Document):
    collection = 'user'
    name = StringField(maxlen=255)
    email = EmailField(maxlen=512)
