import re


class Field:
    value = None

    def __init__(self, required=True, default=None):
        self.required = required
        self.default = default

    def set_value(self, value):
        self.value = value

    def is_valid(self):
        return True

    def get(self):
        if self.value is None and self.default is not None:
            return self.default()
        return self.value


class StringField(Field):
    def __init__(self, maxlen=None, **kwargs):
        super().__init__(**kwargs)
        self.maxlen = maxlen

    def is_valid(self) -> bool:
        value = self.get()
        if not isinstance(value, str):
            return False
        if not self.maxlen:
            return True
        return len(value) <= self.maxlen


class EmailField(StringField):
    def is_valid(self) -> bool:
        if not super().is_valid():
            return False
        if not re.match(r'^[\w]+@[\w]+\.[\w+]{1,3}$', self.get()):
            return False
        return True


class IntegerField(Field):
    def is_valid(self) -> bool:
        return isinstance(self.get(), int)
