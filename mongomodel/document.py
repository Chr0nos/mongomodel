from typing import List
from bson import ObjectId
import pymongo
# from . import db
from . import db, Field


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
        self._copy_fields()
        for key, value in kwargs.items():
            setattr(self, key, value)

    def _copy_fields(self) -> None:
        """Fields needs to be differents object from the main class declaration
        to prevent instance_a to taint on instance_b
        """
        for field_name in self.fields:
            field = object.__getattribute__(self, field_name)
            object.__setattr__(self, field_name, field.copy())

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
            attribute.set_value(value)
            return
        super().__setattr__(name, value)
        if isinstance(value, Field) and name not in self.fields:
            self.fields.append(name)

    def __delattr__(self, name):
        if name in self.fields:
            self.fields.remove(name)
        super().__delattr__(name)

    def save(self, session=None):
        """Update or insert the current document to the database if needed
        then return the response from the database
        """
        if not self.is_valid():
            raise DocumentInvalidError
        collection = self.get_collection()
        if not self._id:
            response = collection.insert_one(self.to_dict(), session=session)
            self._id = response.inserted_id
            return response
        return collection.update_one({'_id': self._id},
                                     {'$set': self.to_dict()},
                                     session=session)

    def commit(self, **kwargs):
        """Perform a `.save()` but return self insead of the database response
        """
        self.save(**kwargs)
        return self

    def delete(self, session=None):
        """Remove the current document from the database if already present
        the _id is used to know if the document is in db.
        """
        if self._id is None:
            return
        response = self.get_collection().delete_one(
            {'_id': self._id}, session=session)
        self._id = None
        return response

    def refresh(self, session=None):
        """Reload the current id from the database, if no id is available a
        ValueError will be raised.
        """
        if not self._id:
            raise ValueError('id')
        response: dict = self.get_collection().find_one({'_id': self._id},
                                                        session=session)
        self.update(**response)
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
    def from_id(cls, document_id: ObjectId, collection=None) -> 'Document':
        collection = collection if collection else cls.collection
        resource = db[collection].find_one({'_id': document_id})
        if not resource:
            raise DocumentNotFoundError
        document = cls(**resource, collection=collection)
        return document

    def copy(self) -> 'Document':
        """Returns a new instance of the current class, also make a copy of
        each fields in the document
        """
        fields = {name: object.__getattribute__(self, name).copy()
                  for name in self.fields}
        doc = type(self)(collection=self.collection, **fields)
        return doc

    def clear(self) -> 'Document':
        for field in self.fields:
            setattr(self, field, None)
        return self

    def update(self, **kwargs) -> 'Document':
        for k, v in kwargs.items():
            setattr(self, k, v)
        return self

    def __iter__(self):
        for field_name in self.fields:
            yield field_name, getattr(self, field_name)

    @classmethod
    def find(cls, filter: dict = None, sort=None, limit=None,
            **kwargs) -> List['Document']:
        cursor = cls.get_collection().find(kwargs)
        if sort:
            cursor = cursor.sort(sort)
        if limit:
            cursor = cursor.limit(limit)
        return [cls(**item) for item in cursor]

    @classmethod
    def find_raw(cls, search: dict = None) -> pymongo.cursor.Cursor:
        """Peforms a search in the database in raw mode: no Document will be
        created, all fields will be visible, use this for debugging purposes.
        """
        return cls.get_collection().find(search if search else {})

    @classmethod
    def get_collection(cls) -> pymongo.collection.Collection:
        collection: str = getattr(cls, 'collection')
        if not collection:
            collection = cls.__name__.lower()
        return db[collection]

    @classmethod
    def insert_many(cls, documents: List['Document'],
                    session=None) -> List['Document']:
        """Insert all valids documents given, will not not raise error on
        invalid ones but will not insert them, instead this function return the
        list of inserted items, it will also populate then with an ._id
        """
        insert_list = [doc for doc in documents if doc.is_valid()]

        result = cls.get_collection().insert_many(
            [doc.to_dict() for doc in insert_list],
            session=session
        )

        for doc, objectid in zip(insert_list, result.inserted_ids):
            doc._id = objectid
        return insert_list

    @classmethod
    def drop(cls, session=None) -> None:
        """Drop the whole collection related to this class
        """
        cls.get_collection().drop(session=session)

    @classmethod
    def delete_many(cls, documents: List['Document'],
                    session=None) -> List['Document']:
        doclist = dict({doc._id: doc for doc in documents})
        cls.get_collection().delete_many(
            {'_id': {'$in': list(doclist.keys())}},
            session=session
        )
        for doc in doclist.values():
            doc._id = None
        return documents
