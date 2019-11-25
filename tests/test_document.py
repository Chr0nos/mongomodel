import pytest
from mock import patch, MagicMock

from bson import ObjectId
from document import (
    Document, Field, DocumentInvalidError, DocumentNotFoundError)
from datetime import datetime

from functools import wraps


def no_database(func):
    """Mock the main collection resolution for the database access
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        with patch('document.db.__getitem__') as collection:
            collection.return_value = None
            func(*args, **kwargs)
    return wrapper


class InvalidField(Field):
    def is_valid(self):
        return False


class TestDocument:
    def test_document_init_not_crashing(self):
        class User(Document):
            collection = 'test'

        User()

    @no_database
    def test_document_with_kwargs(self):
        class User(Document):
            collection = 'test'
            name = Field()

        user = User(name='toto')
        assert user.name == 'toto'

    @no_database
    def test_fields_resolution(self):
        class TestDocument(Document):
            collection = 'test'
            name = Field()
            age = Field()
            useless = 'test'
            ignoreme = 42

        doc = TestDocument()
        missing = ['name', 'age']
        for field in doc.fields:
            assert field in missing
            missing.remove(field)
        assert not missing, missing

    @patch('document.db')
    def test_from_id(self, mock_db):
        test_dict = {'test': True}
        mock_db.__getitem__.return_value.find_one.return_value = test_dict
        doc = Document.from_id('test')
        assert isinstance(doc, Document)

    @patch('document.db')
    def test_from_unknow_id(self, mock_db):
        mock_db.__getitem__.return_value.find_one.return_value = None
        with pytest.raises(DocumentNotFoundError):
            Document.from_id('test')

    @patch('document.db')
    def test_save_new(self, mock_db):
        insert: MagicMock = mock_db.__getitem__.return_value.insert_one
        insert.return_value.inserted_id.return_value = 42
        doc = Document()
        doc.save()
        insert.assert_called_once_with({})

    @patch('document.db')
    def test_save_old(self, mock_db):
        update: MagicMock = mock_db.__getitem__.return_value.update_one
        doc = Document(_id='test')
        doc.save()
        update.assert_called_once()
        assert doc._id == 'test'

    @no_database
    def test_save_invalid(self):
        doc = Document(collection='test')
        doc.is_valid = lambda: False
        with pytest.raises(DocumentInvalidError):
            doc.save()

    @no_database
    def test_delete_unknow(self):
        doc = Document(collection='test')
        assert doc.delete() is None

    @patch('document.db')
    def test_delete_legit(self, mock_db):
        delete_one = mock_db.__getitem__.return_value.delete_one
        delete_one.return_value = True
        doc = Document(_id='foo')
        doc.delete()
        assert doc._id is None
        delete_one.assert_called_once_with({'_id': 'foo'})

    @no_database
    def test_refresh_without_id(self):
        doc = Document(collection='test')
        with pytest.raises(ValueError):
            doc.refresh()

    @patch('document.db')
    def test_refresh_legit(self, mock_db):
        find_one = mock_db.__getitem__.return_value.find_one
        find_one.return_value = {'test': True}
        doc = Document(_id=42)
        doc.test = Field()
        doc.refresh()
        find_one.assert_called_once_with({'_id': 42})
        assert doc.test is True

    @patch('document.db')
    def test_find(self, mock_db):
        find = mock_db.__getitem__.return_value.find
        find.return_value = [{'_id': docid} for docid in range(10)]
        response = list(Document(collection='test').find())
        assert len(response) == 10
        for index, doc_dict in enumerate(response):
            assert doc_dict['_id'] == index
        find.assert_called()

    @patch('document.db')
    def test_find_one(self, mock_db):
        test_doc = {'_id': 54266}
        find_one = mock_db.__getitem__.return_value.find_one
        find_one.return_value = test_doc
        response = Document(collection='test').find(match=test_doc, one=True)
        find_one.assert_called_once_with(test_doc)
        assert response == test_doc

    @no_database
    def test_fields_append(self):
        doc = Document(collection='test')
        assert doc.fields == []
        doc.name = Field(default=lambda: 'alpha')
        doc.age = Field(default=lambda: 'bravo')
        assert doc.fields == ['name', 'age']
        assert doc.name == 'alpha'
        assert doc.age == 'bravo'

    @no_database
    def test_to_dict(self):
        doc = Document(collection='test')
        doc.creation_date = Field(default=lambda: datetime.now().isoformat())
        doc.name = Field()
        doc.name = 'tomtom'
        doc_dict = doc.to_dict()
        assert 'creation_date' in doc_dict
        assert 'collection' not in doc_dict
        assert doc_dict['name'] == 'tomtom'
        assert len(doc_dict) == 2

    @no_database
    def test_del_field_attribute(self):
        class Vector(Document):
            collection = 'test'

            def __init__(self, **kwargs):
                self.x = Field()
                self.y = Field()
                super().__init__(**kwargs)

        vec = Vector()
        assert 'x' in vec.fields
        assert 'y' in vec.fields
        del vec.x
        assert 'x' not in vec.fields
        assert 'y' in vec.fields

    @no_database
    def test_invalid_fields(self):
        doc = Document(collection='test')
        doc.foo = InvalidField()
        doc.bar = InvalidField()
        doc.ham = Field()
        invalid_fields = doc.invalid_fields()
        for field_name in ('foo', 'bar'):
            assert field_name in invalid_fields
            invalid_fields.remove(field_name)
        assert len(invalid_fields) == 0

    @no_database
    def test_is_valid(self):
        doc = Document(collection='test')
        doc.foo = Field()
        assert doc.is_valid() is True
        del doc.foo
        doc.foo = InvalidField()
        assert doc.is_valid() is False

    @patch('document.db')
    def test_agnostic_retrive(self, db):
        response = {
            '_id': ObjectId(),
            'name': 'fight club',
            'nested': {
                'a': [1, 2, 3],
                'b': True
            }
        }
        db.__getitem__.return_value.find_one.return_value = response

        class Book(Document):
            name = Field()
            nested = Field()

        book = Book(collection='test', _id=42)
        book.refresh()
        assert book.name == response['name']
        assert book.nested['a'] == response['nested']['a']
        assert book.nested['b'] == response['nested']['b']

    @no_database
    def test_copy(self):
        doc = Document(collection='test', _id='abcdef')
        doc.name = Field(value='named test', default=lambda: 'tested')
        cpy = doc.copy()
        assert doc != cpy
        assert doc.name == cpy.name
        cpy.name = None
        assert cpy.name == 'tested'
        assert doc.name == 'named test'
        assert cpy._id is None
        assert cpy.collection == doc.collection

    @no_database
    def test_load_dict(self):
        original = Document(collection='test')
        original.name = Field(value='named test')
        original.age = Field(value=12)
        cpy = original.copy().load_dict({'name': 'bibou', 'age': 30})
        assert cpy.name == 'bibou'
        assert original.name == 'named test'
        assert original.age == 12
        assert cpy.age == 30
