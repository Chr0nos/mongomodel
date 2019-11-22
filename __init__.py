import pymongo


client = pymongo.MongoClient(host='10.8.0.1')
db: pymongo.database.Database = client.test
