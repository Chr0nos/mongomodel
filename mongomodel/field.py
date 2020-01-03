import re
from datetime import datetime


class Field:
    """A field is a basic description of a database document part,
    a default field is allways considered as valid.
    """
    value = None

    def __init__(self, value=None, required=True, default=None):
        self.required = required
        self.default = default
        self.set_value(value)

    def set_value(self, value):
        self.value = value

    def is_valid(self) -> bool:
        try:
            self.check()
            return True
        except (ValueError, TypeError):
            return False

    def check(self):
        pass

    def get(self):
        """Returns the current value of the field, depending of a default or
        the real value if available.
        """
        if self.value is None and self.default is not None:
            return self.default()
        return self.value

    def copy(self, **kwargs):
        field = type(self)(value=self.value, required=self.required,
                           default=self.default, **kwargs)
        return field


class StringField(Field):
    def __init__(self, maxlen=None, **kwargs):
        super().__init__(**kwargs)
        self.maxlen = maxlen

    def copy(self):
        instance = super().copy()
        instance.maxlen = self.maxlen
        instance.value = f'{self.value}' if self.value is not None else None
        return instance

    def check(self):
        value = self.get()
        if not isinstance(value, str):
            raise TypeError(value, type(value))
        if self.maxlen and len(value) > self.maxlen:
            raise ValueError(value)


class EmailField(StringField):
    def check(self) -> None:
        super().check()
        value = self.get()
        if not re.match(r'^[\w\.]+@[\w.]+\.[a-z]{2,3}$', value):
            raise ValueError(value)


class IntegerField(Field):
    def check(self) -> None:
        value = self.get()
        if not isinstance(value, int) or type(value) is bool:
            raise ValueError(value)


class TypeField(Field):
    """Just enforce an object type, it can be scallar or not, just be carefull
    that mongodb can store it.

    example: TypeField(required_type=datetime, default=lambda: datetime.now())
    """
    def __init__(self, *args, required_type: type, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = required_type

    def check(self) -> None:
        value = self.get()
        if self.type is None:
            if value is not None:
                raise ValueError(value)
        elif not isinstance(value, self.type):
            raise ValueError(value)

    def copy(self):
        return super().copy(required_type=self.type)


class FloatField(TypeField):
    def __init__(self, *args, **kwargs):
        kwargs.pop('required_type', None)
        super().__init__(*args, required_type=float, **kwargs)


class DateTimeField(TypeField):
    def __init__(self, *args, **kwargs):
        kwargs['required_type'] = datetime
        super().__init__(*args, **kwargs)


class BoolField(TypeField):
    def __init__(self, *args, **kwargs):
        kwargs['required_type'] = bool
        super().__init__(*args, **kwargs)


class RegexField(StringField):
    def __init__(self, regex: str, **kwargs):
        super().__init__(**kwargs)
        self.regex = re.compile(regex)
        self.rule = regex

    def check(self) -> None:
        super().check()
        value = self.get()
        if not self.regex.match(value):
            raise ValueError(value)

    def copy(self):
        instance = super().copy()
        instance.rule = f'{self.rule}'
        instance.regex = re.compile(self.rule)
        return instance
