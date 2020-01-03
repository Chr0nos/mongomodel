from mongomodel import setup_database
from mock import patch


class TestConf:
    @patch('mongomodel.conf.pymongo.MongoClient')
    def test_conf_basic(self, mock_client):
        client_instance = object()
        mock_client.__getitem__ = lambda self: client_instance

        setup_database('127.0.0.1', 'test')
