from mongomodel.tools import dict_deep_update, merge_values


class TestDeepUpdate:
    def test_basic(self):
        data = {}
        dict_deep_update(data, {'some': 'value'})
        assert data['some'] == 'value'

    def test_nested(self):
        data = {'age': 30}
        dict_deep_update(data, {'age': {'nested': True}},
                         on_conflict=merge_values)
        assert data['age']['$eq'] == 30
        assert data['age']['nested'] == True
