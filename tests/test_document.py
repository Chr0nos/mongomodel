import pytest
from mock import patch, MagicMock

from document import Document, Field, DocumentInvalidError


class TestDocument:
    def test_document_init_not_crashing(self):
        class User(Document):
            collection = 'test'

        User()

    @patch('document.db')
    def test_document_with_kwargs(self, mock_db):
        mock_db.__getitem__.return_value = None

        class User(Document):
            name = Field()

        user = User(name='toto')
        assert user.name == 'toto'

    @patch('document.db')
    def test_fields_resolution(self, mock_db):
        mock_db.__getitem__.return_value = None

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
    def test_save_new(self, mock_db):
        insert: MagicMock = mock_db.__getitem__.return_value.insert_one
        insert.return_value.inserted_id.return_value = 42
        doc = Document()
        doc.save()
        insert.assert_called_once_with({})

    @patch('document.db')
    def test_save_invalid(self, mock_db):
        mock_db.__getitem__.return_value = None
        doc = Document()
        doc.is_valid = lambda: False
        with pytest.raises(DocumentInvalidError):
            doc.save()

    @patch('document.db')
    def test_delete_unknow(self, mock_db):
        doc = Document()
        assert doc.delete() is None

    @patch('document.db')
    def test_delete_legit(self, mock_db):
        delete_one = mock_db.__getitem__.return_value.delete_one
        delete_one.return_value = True
        doc = Document(_id='foo')
        doc.delete()
        assert doc._id is None
        delete_one.assert_called_once_with({'_id': 'foo'})

    @patch('document.db')
    def test_refresh_without_id(self, mock_db):
        mock_db.__getitem__.return_value = None
        doc = Document()
        with pytest.raises(ValueError):
            doc.refresh()

    @patch('document.db')
    def test_refresh_legit(self, mock_db):
        find_one = mock_db.__getitem__.return_value.find_one
        find_one.return_value = {'test': True}
        doc = Document(_id=42)
        doc.test = Field()
        doc.fields_discover()
        doc.refresh()
        find_one.assert_called_once_with({'_id': 42})
        assert doc.test == True

    @patch('document.db')
    def test_find(self, mock_db):
        find = mock_db.__getitem__.return_value.find
        find.return_value = [{'_id': docid} for docid in range(10)]
        response = list(Document.find())
        assert len(response) == 10
        for index, doc_dict in enumerate(response):
            assert doc_dict['_id'] == index
        find.assert_called()

    @patch('document.db')
    def test_find_one(self, mock_db):
        test_doc = {'_id': 54266}
        find_one = mock_db.__getitem__.return_value.find_one
        find_one.return_value = test_doc
        response = Document.find(match=test_doc, one=True)
        find_one.assert_called_once_with(test_doc)
        assert response == test_doc


class TestField:
    def test_is_valid(self):
        field = Field()
        assert field.is_valid()

    @pytest.mark.parametrize('value', ('yes', 42, False, None))
    def test_set_value(self, value):
        field = Field()
        field.set_value(value)
        assert field.value == value

