import mongomodel
from datetime import datetime


class User(mongomodel.Document):
    age = mongomodel.IntegerField(required=False)
    email = mongomodel.StringField(maxlen=100)
    name = mongomodel.StringField(maxlen=100)
    created = mongomodel.Field(default=lambda: datetime.now())
    is_admin = mongomodel.TypeField(value=False, required_type=bool)

    def __repr__(self):
        return f'<User {self.name}> {self.email}'

    def pre_save(self, content, is_new):
        self.created = content['created']
