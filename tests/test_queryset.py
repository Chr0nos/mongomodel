import pytest

from mock import patch
from mongomodel.queryset import QuerySet


class TestQuerySet:
    def test_instanciate_and_delete(self):
        qs = QuerySet()
        del qs

    def test_queryset_copy(self):
        a = QuerySet()
        b = a.copy()
        assert a is not b

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

    @pytest.mark.skip('work in progress')
    @patch('mongomodel.queryset.QuerySet', spec=True)
    def test_count(self, mock_model):
        count = mock_model.model.get_collection.return_value.count_documents
        count.return_value = 1234
        response = mock_model('test').count()
        assert response == 1234
        count.assert_called_once()
