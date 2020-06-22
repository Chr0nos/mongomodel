import pymongo
from pymongo import MongoClient


def setup_database(hostname='10.8.0.1', database='test', **kwargs):
    import mongomodel

    kwargs.setdefault('connect', False)
    client = MongoClient(host=hostname, **kwargs)
    mongomodel.client = client
    mongomodel.db = client[database]
    mongomodel.document.db = mongomodel.db
