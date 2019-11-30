import pytest
from field import Field, StringField, EmailField, IntegerField, RegexField


class TestField:
    def test_is_valid(self):
        field = Field()
        assert field.is_valid()

    @pytest.mark.parametrize('value', ('yes', 42, False, None))
    def test_set_value(self, value):
        field = Field()
        field.set_value(value)
        assert field.value == value

    @pytest.mark.parametrize('value, required, default', (
        (0, True, None),
        (42, False, lambda: -1),
        (None, False, None)
    ))
    def test_copy(self, value, required, default):
        field = Field(value=value, required=required, default=default)
        cpy = field.copy()
        assert field != cpy
        assert field.value == cpy.value
        assert field.get() == cpy.get()
        assert field.required == cpy.required


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
                                        'author@student.42.fr',
                                        'mark@sub.domain.inside.org',
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
        1.0,
        'blah@nope',
        '..',
        'a@b@.fr',
        ''
    ))
    def test_invalid(self, email):
        field = EmailField(maxlen=30)
        field.set_value(email)
        assert field.is_valid() is False


class TestIntegerField:
    @pytest.mark.parametrize('value, valid', [
        (0, True),
        (1, True),
        (-42, True),
        (1.0, False),
        ('Hi', False),
        (True, False),
        (False, False),
        (None, False)
    ])
    def test_fields(self, value, valid):
        field = IntegerField()
        field.set_value(value)
        assert field.is_valid() is valid


class TestRegexField:
    def test_inheritance(self):
        field = RegexField(r'')
        assert isinstance(field, StringField)

    @pytest.mark.parametrize('rule, value', [
        (r'^\w+$', 'test'),
        (r'^\d+$', '0123456789'),
        (r'^[abc]+$', 'abcaaac')
    ])
    def test_check(self, rule, value):
        field = RegexField(rule, value=value)
        field.check()

    @pytest.mark.parametrize('rule, value', [
        (r'^\d+$', 'test'),
        (r'^\w$', 'te st'),
    ])
    def test_invalid(self, rule, value):
        field = RegexField(rule, value=value)
        with pytest.raises(ValueError):
            field.check()
