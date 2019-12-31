import mongomodel
from random import randint


class Point(mongomodel.Document):
    x = mongomodel.IntegerField(default=lambda: randint(0, 1000))
    y = mongomodel.IntegerField(default=lambda: randint(0, 1000))
    z = mongomodel.IntegerField(default=lambda: randint(0, 1000))

    def __str__(self):
        return f'x: {self.x} y: {self.y} z: {self.z}'

    def __repr__(self):
        return str(self)

    def __add__(self, b):
        return Point(x=self.x + b.x, y=self.y + b.y, z=self.z + b.z)
