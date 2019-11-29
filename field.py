import re


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

    def copy(self):
        field = type(self)(value=self.value, required=self.required,
                           default=self.default)
        return field


class StringField(Field):
    def __init__(self, maxlen=None, **kwargs):
        super().__init__(**kwargs)
        self.maxlen = maxlen

    def copy(self):
        instance = super().copy()
        instance.maxlen = self.maxlen
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
