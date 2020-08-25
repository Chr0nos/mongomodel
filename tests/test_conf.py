from mongomodel import database
from mock import patch


class TestConf:
    @patch('mongomodel.conf.pymongo.MongoClient')
    def test_conf_basic(self, mock_client):
        client_instance = object()
        mock_client.__getitem__ = lambda self: client_instance

        database.connect(host='127.0.0.1', db='test')
