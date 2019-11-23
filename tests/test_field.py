import pytest
from field import Field, StringField, EmailField


class TestField:
    def test_is_valid(self):
        field = Field()
        assert field.is_valid()

    @pytest.mark.parametrize('value', ('yes', 42, False, None))
    def test_set_value(self, value):
        field = Field()
        field.set_value(value)
        assert field.value == value


class TestStringField:
    @pytest.mark.parametrize('text', ('This is valid !', '0123456789', ''))
    def test_valid_string(self, text):
        field = StringField(maxlen=50)
        field.set_value(text)
        assert field.is_valid()
        assert field.get() == text

    @pytest.mark.parametrize('item', (0, None, False, True, 1.0))
    def test_invalid(self, item):
        field = StringField(maxlen=42)
        field.set_value(item)
        assert field.is_valid() is False

    def test_too_long(self):
        field = StringField(maxlen=10)
        field.set_value('-' * 10)
        assert field.is_valid()
        field.set_value('-' * 11)
        assert field.is_valid() is False

    def test_without_maxlen(self):
        field = StringField()
        field.set_value('-' * 512)
        assert field.is_valid()


class TestEmailField:
    @pytest.mark.parametrize('email', (
                                        'test@free.fr',
                                        'thing@gmail.be',
                                        # 'author@student.42.fr',
                                        'a@b.cd'
    ))
    def test_valid(self, email):
        field = EmailField(maxlen=100)
        field.set_value(email)
        assert field.is_valid()

    @pytest.mark.parametrize('email', (
        42,
        'foo',
        None,
        False, True,
        1.0
    ))
    def test_invalid(self, email):
        field = EmailField(maxlen=30)
        field.set_value(email)
        assert field.is_valid() is False
