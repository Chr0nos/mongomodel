import pytest
from field import Field


class TestField:
    def test_is_valid(self):
        field = Field()
        assert field.is_valid()

    @pytest.mark.parametrize('value', ('yes', 42, False, None))
    def test_set_value(self, value):
        field = Field()
        field.set_value(value)
        assert field.value == value

