def setup_database(hostname='10.8.0.1', database='test', **kwargs):
    import mongorm, pymongo

    client = pymongo.MongoClient(host=hostname, connect=False, **kwargs)
    mongorm.client = client
    mongorm.db = client[database]
    mongorm.document.db = mongorm.db
