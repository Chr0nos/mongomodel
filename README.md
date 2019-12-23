# MongOrm
## Description
This project is a tiny ORM in python3 for mongodb.
Each database entry is a `Document` and each document has `Fields`

## Getting started
```shell
git clone git@github.com:Chr0nos/mongorm.git
virtualenv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

then the in the code
```python
import mongorm

mongorm.setup_database(hostname='something', database='test')
# now you can use the orm.
```

## Example
### Create
To create a new document model you have to make a new class from `Document`
```python
import mongorm


class User(monhorm.Document):
	collection = 'user'
	name = mongorm.StringField(maxlen=255)
	email = mongorm.EmailField(maxlen=255)
	level = mongorm.IntegerField()
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

## Update
To update a document you just have to perform a `document.save()`, it will
update the document if it's already present in database.

## Delete
Use `document.delete()`

## Dynamic model creation
In some circumstancies you don't know the excat shape of a model at parsetime,
so it's possible to edit a model, the new field(s) has to be an instance of `Field`

```python
user.specific_information = Field(value='whatever')
```

## Remove fields
you can delete the class attribute with
```python
del user.name
```

## Transform to dict
```python
user.to_dict()
```

## Get all fields name for a document
```python
user.fields
```
returns a list of `str`


## Create a document from an other
```python
cpy = user.copy()
cpy.kind = StringField(value='artist', maxlen='20')
```
the copied document wil have it's own `Fields`


## Load a document from it's ID
```python
from bson import ObjectId

user = User.from_id(ObjectId('012345678'))
```


## Reset all fields to default
```python
user.clear()
```


## Reload from database
```python
user.refresh()
```


### Default fields
If you won't filter what kind of data can be set into a field, just use the
main class `Field` wich is allways considered as valid.

it's possible to have default values if the field stay at a `None` state

```python
from mongorm.document import Document
from mongorm.field import Field
from datetime import datetime


class Book(mongorm.Document):
	collection = 'book'
	name = mongorm.Field(default=lambda: '')
	creation_date = mongorm.Field(default=lambda: datetime.now().isoformat())

```
I use function to prevent a useless call in case of no value provided.


## Custom field
This is an example of a `last updated` field

```python
from datetime import datetime

class LastUpdateField(mongorm.Field):
	def get(self):
		return datetime.now().isoformat()
```

the `get` method will be called each time you will call the attribute in the
document.

## Custom field validation
```python
class CustomField(mongorm.Field):
	def check(self):
		# you can perform validations here.
		# self.value = the current value
		# self.get() = the value OR it's default if available
		pass
```


## Extra fields from database
All fields that are not defined into the model/document will be available in
readonly.


## Create many documents at once
```python
books: List[Book] = [
	Book(name='mongodb'),
	Book(name='something'),
	...
]
Book.insert_many(books)
```
At this point all inserted (valids) book will have an `_id` property,
In case of invalid documents, no errors will be raised but the document will be
ignored.
