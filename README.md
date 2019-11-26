# MongOrm
## Description
This project is a tiny ORM in python3 for mongodb.
Each database entry is a `Document` and each document has `Fields`

## Example
### Create
To create a new document model you have to make a new class from `Document`
```python
from mongorm.document import Document
from mongorm.field import StringField, EmailField, IntegerField, Field

class User:
    name = StringField(maxlen=255)
	email = EmailField(maxlen=255)
	level = IntegerField()
```

then you can instanciate a new user in two ways:
```python
user = User()
user.name = 'john doe'
user.level = 2
user.email = 'something@test.com'
user.save()
```

or with the constructor:
```python
user = User(name='john doe', email='something@test.com', level=2)
user.save()
```

in case of an invalid model, example:
```python
user.name = 123
user.save()
```

an `DocumentInvalidError` will be raised.

