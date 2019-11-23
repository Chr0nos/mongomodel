import re


class Field:
    value = None

    def set_value(self, value):
        self.value = value

    def is_valid(self):
        return True


class StringField(Field):
    def __init__(self, maxlen=None):
        self.maxlen = maxlen

    def is_valid(self) -> bool:
        if not isinstance(self.value, str):
            return False
        if not self.maxlen:
            return True
        return len(self.value) <= self.maxlen


class EmailField(StringField):
    def is_valid(self) -> bool:
        if not super().is_valid():
            return False
        if not re.match(r'^[\w]+@[\w]+\.[\w+]{1,3}$', self.value):
            return False
        return True


class IntegerField(Field):
    def is_valid(self) -> bool:
        return isinstance(self.value, int)


