from typing import List
from bson import ObjectId
import pymongo
# from . import db
from field import Field

client = pymongo.MongoClient(host='10.8.0.1', connect=False)
db: pymongo.database.Database = client.test


class DocumentNotFoundError(Exception):
    pass


class DocumentInvalidError(Exception):
    pass


class Document:
    _id: ObjectId = None
    collection: str = None
    fields: List[str] = []

    def __init__(self, collection=None, **kwargs):
        self._id = kwargs.pop('_id', None)
        self.fields_discover()
        if collection:
            self.collection = collection
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.cursor = db[self.collection]

    def fields_discover(self):
        # discover class fields
        self.fields = list(filter(
            lambda x: isinstance(object.__getattribute__(self, x), Field),
            dir(self)
        ))

    def __getattribute__(self, name):
        attribute = super().__getattribute__(name)
        if isinstance(attribute, Field):
            return attribute.get()
        return attribute

    def __setattr__(self, name, value):
        try:
            attribute = self.raw_attr(name)
        except AttributeError:
            attribute = None
        # updaging a current field
        if attribute and isinstance(attribute, Field):
            if name not in self.fields:
                self.fields.append(name)
            attribute.set_value(value)
            return
        super().__setattr__(name, value)
        if isinstance(value, Field) and name not in self.fields:
            self.fields.append(name)

    def __delattr__(self, name):
        if name in self.fields:
            self.fields.remove(name)
        super().__delattr__(name)

    def save(self):
        """Update or insert the current document to the database if needed
        then return the response from the database
        """
        if not self.is_valid():
            raise DocumentInvalidError
        if not self._id:
            response = self.cursor.insert_one(self.to_dict())
            self._id = response.inserted_id
            return response
        return self.cursor.update_one({'_id': self._id}, self.to_dict())

    def delete(self):
        """Remove the current document from the database if already present
        the _id is used to know if the document is in db.
        """
        if self._id is None:
            return
        response = self.cursor.delete_one({'_id': self._id})
        self._id = None
        return response

    def refresh(self):
        """Reload the current id from the database, if no id is available a
        ValueError will be raised.
        """
        if not self._id:
            raise ValueError('id')
        response: dict = self.cursor.find_one({'_id': self._id})
        for k in self.fields:
            setattr(self, k, response.get(k))
        return self

    def to_dict(self) -> dict:
        return dict({k: getattr(self, k) for k in self.fields})

    def raw_attr(self, name):
        """Allow retrive of a raw field attribute instead of it's value
        """
        return super().__getattribute__(name)

    def is_valid(self) -> bool:
        for field_name in self.fields:
            field = object.__getattribute__(self, field_name)
            if not field.is_valid():
                return False
        return True

    def invalid_fields(self) -> List[str]:
        """Return a list of all invalid fields for this document.
        in case of a valid document then an empty list will be returned.
        """
        invalids = []
        for field_name in self.fields:
            field = self.raw_attr(field_name)
            if not field.is_valid():
                invalids.append(field_name)
        return invalids

    @classmethod
    def from_id(cls, document_id: ObjectId):
        resource = db[cls.collection].find_one({'_id': document_id})
        if not resource:
            raise DocumentNotFoundError
        document = cls(**resource)
        return document

    @classmethod
    def find(cls, match=None, one=False, **kwargs):
        if match is None:
            match = {}
        func = getattr(db[cls.collection], 'find' if not one else 'find_one')
        return func(match, **kwargs)
