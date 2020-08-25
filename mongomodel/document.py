from typing import List
from bson import ObjectId
import pymongo

from . import Field
from .queryset import QuerySet


class DocumentMeta(type):
    """Meta class of `Document`, allow to automaticaly set a QuerySet in Objects
    attribute.
    """
    def __new__(cls, name, bases, optdict):
        instance = super().__new__(cls, name, bases, optdict)
        manager = getattr(instance, 'objects', None)
        if not manager:
            instance.objects = QuerySet(instance)
        else:
            manager.model = instance

        # declaration of thoses errors here to have proper errors per
        # documents kinds instead of global ones
        class DocumentError(Exception):
            pass

        class DoesNotExist(DocumentError):
            pass

        class DocumentInvalid(DocumentError):
            pass

        instance.DocumentError = DocumentError
        instance.DoesNotExist = DoesNotExist
        instance.DocumentInvalid = DocumentInvalid

        return instance


class Document(metaclass=DocumentMeta):
    _id: ObjectId = None
    collection: str = None
    fields: List[str] = []
    objects: QuerySet = None

    def __init__(self, collection=None, **kwargs):
        self._id = kwargs.pop('_id', None)
        self.fields_discover()
        if collection:
            self.collection = collection
        self._copy_fields()
        for key, value in kwargs.items():
            setattr(self, key, value)


    def __str__(self):
        if self._id:
            return str(self._id)
        return ''

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self}>'

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

    def pre_save(self, content: dict, is_new=False) -> None:
        """Called just before calling the database to send the document
        content is all fields formated and ready for the database, including
        default values
        """
        pass

    def save(self, session=None):
        """Update or insert the current document to the database if needed
        then return the response from the database
        """
        if not self.is_valid():
            raise self.DocumentInvalid(self.invalid_fields())
        collection = self.objects.get_collection()
        document_content = self.to_dict()
        self.pre_save(document_content, self._id is None)
        if not self._id:
            response = collection.insert_one(document_content, session=session)
            self._id = response.inserted_id
            return response
        return collection.update_one({'_id': self._id},
                                     {'$set': document_content},
                                     session=session)

    def commit(self, **kwargs) -> 'Document':
        """Perform a `.save()` but return self insead of the database response
        """
        self.save(**kwargs)
        return self

    def delete(self, session=None) -> pymongo.collection.DeleteResult:
        """Remove the current document from the database if already present
        the _id is used to know if the document is in db.
        """
        if self._id is None:
            return
        response = self.objects.get_collection().delete_one(
            {'_id': self._id}, session=session)
        self._id = None
        return response

    def refresh(self, session=None) -> 'Document':
        """Reload the current id from the database, if no id is available a
        ValueError will be raised.
        """
        if not self._id:
            raise ValueError('id')

        response = self.objects \
            .get_collection().find_one({'_id': self._id}, session=session)
        self.update(**response)
        return self

    def to_dict(self) -> dict:
        return dict({k: getattr(self, k) for k in self.fields})

    def raw_attr(self, name):
        """Allow retrive of a raw field attribute instead of it's value
        """
        return super().__getattribute__(name)

    def is_valid(self, raises=False) -> bool:
        for field_name in self.fields:
            field = object.__getattribute__(self, field_name)
            if not field.is_valid() and field.required:
                if raises:
                    raise self.DocumentInvalid(self._id)
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
        resource = cls.objects.get_collection().find_one({'_id': document_id})
        if not resource:
            raise cls.DoesNotExist(document_id)
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
    def insert_many(cls, documents: List['Document'],
                    session=None) -> List['Document']:
        """Insert all valids documents given, will not not raise error on
        invalid ones but will not insert them, instead this function return the
        list of inserted items, it will also populate then with an ._id
        """
        insert_list = [doc for doc in documents if doc.is_valid()]

        result = cls.objects.get_collection().insert_many(
            [doc.to_dict() for doc in insert_list],
            session=session
        )

        for doc, objectid in zip(insert_list, result.inserted_ids):
            doc._id = objectid
        return insert_list

    @classmethod
    def delete_many(cls, documents: List['Document'],
                    session=None) -> List['Document']:
        doclist = dict({doc._id: doc for doc in documents})
        cls.objects.get_collection().delete_many(
            {'_id': {'$in': list(doclist.keys())}},
            session=session
        )
        for doc in doclist.values():
            doc._id = None
        return documents
