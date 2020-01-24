import pytest
from mock import patch, MagicMock

from bson import ObjectId
from mongomodel import Document, Field
from datetime import datetime

from functools import wraps


def no_database(func):
    """Mock the main collection resolution for the database access
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        with patch('mongomodel.document.db.__getitem__') as collection:
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

    @patch('mongomodel.document.db')
    def test_from_id(self, mock_db):
        test_dict = {'test': True}
        mock_db.__getitem__.return_value.find_one.return_value = test_dict
        doc = Document.from_id('test')
        assert isinstance(doc, Document)

    @patch('mongomodel.document.db')
    def test_from_unknow_id(self, mock_db):
        mock_db.__getitem__.return_value.find_one.return_value = None
        with pytest.raises(Document.DoesNotExist):
            Document.from_id('test')

    @patch('mongomodel.document.db')
    def test_save_new(self, mock_db):
        insert: MagicMock = mock_db.__getitem__.return_value.insert_one
        insert.return_value.inserted_id.return_value = 42
        doc = Document()
        doc.save()
        insert.assert_called_once_with({}, session=None)

    @patch('mongomodel.document.db')
    def test_save_old(self, mock_db):
        update: MagicMock = mock_db.__getitem__.return_value.update_one
        doc = Document(_id='test')
        doc.save()
        update.assert_called_once_with({'_id': 'test'}, {'$set': {}},
                                       session=None)
        assert doc._id == 'test'

    @no_database
    def test_save_invalid(self):
        doc = Document(collection='test')
        doc.is_valid = lambda: False
        with pytest.raises(Document.DocumentInvalid):
            doc.save()

    @no_database
    def test_delete_unknow(self):
        doc = Document(collection='test')
        assert doc.delete() is None

    @patch('mongomodel.document.db')
    def test_delete_legit(self, mock_db):
        delete_one = mock_db.__getitem__.return_value.delete_one
        delete_one.return_value = True
        doc = Document(_id='foo')
        doc.delete()
        assert doc._id is None
        delete_one.assert_called_once_with({'_id': 'foo'}, session=None)

    @no_database
    def test_refresh_without_id(self):
        doc = Document(collection='test')
        with pytest.raises(ValueError):
            doc.refresh()

    @patch('mongomodel.document.db')
    def test_refresh_legit(self, mock_db):
        find_one = mock_db.__getitem__.return_value.find_one
        find_one.return_value = {'test': True}
        doc = Document(_id=42)
        doc.test = Field()
        doc.refresh()
        find_one.assert_called_once_with({'_id': 42}, session=None)
        assert doc.test is True

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

    @patch('mongomodel.document.db')
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
        assert doc.raw_attr('name') != cpy.raw_attr('name')

    @no_database
    def test_update(self):
        original = Document(collection='test')
        original.name = Field(value='named test')
        original.age = Field(value=12)
        cpy = original.copy()
        cpy.clear()
        cpy.update(name='bibou', age=30)
        assert cpy.name == 'bibou'
        assert original.name == 'named test'
        assert original.age == 12
        assert cpy.age == 30

    @patch('mongomodel.document.db')
    def test_find(self, mock_db):
        class User(Document):
            collection = 'user'
            name = Field()

        mock_db.__getitem__.return_value.find.return_value = (
            {'name': 'seb', '_id': ObjectId()},
            {'name': 'tom', '_id': ObjectId()}
        )
        seb, tom = User.find()
        assert seb.name == 'seb'
        assert tom.name == 'tom'
        assert seb._id != tom._id

    @patch('mongomodel.document.db')
    def test_find_raw(self, mock_db):
        find: MagicMock = mock_db.__getitem__.return_value.find
        find.return_value = None

        class Test(Document):
            collection = 'test'

        Test.find_raw()
        find.assert_called_once()

    @no_database
    def test_iter(self):
        class Test(Document):
            collection = 'test'
            a = Field(value='a1')
            b = Field(value='b1')

        assert list(Test()) == [('a', 'a1'), ('b', 'b1')]

    @patch('mongomodel.document.db')
    def test_drop(self, mock_db):
        mock_drop = mock_db.__getitem__.return_value.drop

        class Test(Document):
            collection = 'dropme'

        Test.drop()
        mock_drop.assert_called_once()

    @pytest.mark.parametrize(
        'items_count, valids_count', (
            (10, 10),
            (10, 5),
            (10, 0),
        )
    )
    @patch('mongomodel.document.db')
    def test_insert_many(self, mock_db, items_count, valids_count):
        insert_many = mock_db.__getitem__.return_value.insert_many

        class Test(Document):
            collection = 'test'
            value = Field()

            def is_valid(self):
                return False

        class FakeInsertManyResponse:
            def __init__(self, items):
                self.inserted_ids = items

        items = list([Test(value='test') for _ in range(items_count)])
        for i in range(valids_count):
            items[i].is_valid = lambda: True

        insert_many.return_value = FakeInsertManyResponse(
            list([ObjectId() for _ in range(valids_count)]))
        inserted = Test.insert_many(items)

        insert_many.assert_called_once()
        assert len(inserted) == valids_count
        for doc in inserted:
            assert doc._id is not None

    @patch('mongomodel.document.db')
    def test_delete_many(self, mock_db):
        delete_many = mock_db.__getitem__.return_value.delete_many
        delete_many.return_value = None

        documents_list = list(
            [Document('test', _id=object()) for _ in range(10)])

        ids = list([doc._id for doc in documents_list])
        Document.delete_many(documents_list)
        delete_many.assert_called_once_with({'_id': {'$in': ids}},
                                            session=None)
        for doc in documents_list:
            assert doc._id is None

    @no_database
    def test_is_valid_with_raises(self):
        field_obj = Field()
        field_obj.is_valid = lambda: False
        doc = Document(collection='test')
        doc.f = field_obj
        with pytest.raises(doc.DocumentInvalid):
            doc.is_valid(raises=True)
