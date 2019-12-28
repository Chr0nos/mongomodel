import pymongo


def setup_database(hostname='10.8.0.1', database='test', **kwargs):
    import mongomodel

    client = pymongo.MongoClient(host=hostname, connect=False, **kwargs)
    mongomodel.client = client
    mongomodel.db = client[database]
    mongomodel.document.db = mongomodel.db
