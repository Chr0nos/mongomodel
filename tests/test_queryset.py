import pytest

from mock import patch, Mock
from mongomodel.queryset import QuerySet


class TestQuerySet:
    def test_instanciate_and_delete(self):
        qs = QuerySet(1234)
        assert qs.model == 1234
        del qs

    def test_queryset_copy(self):
        a = QuerySet('blah')
        b = a.copy()
        assert a is not b
        assert b.model == 'blah'

    def test_read_from_dict(self):
        data = {
            'some': {
                'nested': {
                    'data': 42
                }
            }
        }
        assert QuerySet.read_dict_path(data, ['some', 'nested', 'data']) == 42

    def test_dict_path(self):
        data = QuerySet.dict_path(['some', 'nested', 'data'], 42)
        assert data['some']['nested']['data'] == 42

    def test_sort_instruction(self):
        lst = QuerySet.sort_instruction(['date', '-age', 'a', '-b'])
        assert lst == [('date', 1), ('age', -1), ('a', 1), ('b', -1)]

    def test_count(self):
        fake_model = Mock()
        count = fake_model.get_collection.return_value.count_documents
        count.return_value = 1234
        response = QuerySet(fake_model).count()
        assert response == 1234
        count.assert_called_once()

    @patch('mongomodel.queryset.QuerySet')
    def test_raw(self, mock_qs):
        cursor = object()
        model = Mock()
        model.find_raw.return_value = cursor

        qs = QuerySet(model)
        qs._get_cursor = Mock()
        qs._get_cursor.return_value = cursor
        assert qs.raw(1, ['name'], 3) == cursor
        qs._get_cursor.assert_called_with(cursor, ['name'], 3, 1)

    def test_raw_without_model(self):
        from mongomodel.queryset import MissingModelError

        with pytest.raises(MissingModelError):
            QuerySet().raw()
