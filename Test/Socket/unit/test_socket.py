from time import time
from unittest import TestCase

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import socketio, app
from Utils.Database.modules import Module

# heart_beat_cogs a besoin d'un Module existant en base pour matcher token+fqdn
TEST_MODULE_TOKEN = "37c7e4b5-d40b-3a73-8cb1-804e78959736"
TEST_MODULE_FQDN = "file://"


class TestSocket(TestCase):
    def setUp(self):
        self.client = socketio.test_client(app)

        db_config = app.config['CONFIG_DATA']['database'][0]
        engine = create_engine(
            f"mysql+pymysql://{db_config['username']}:{db_config['password']}@{db_config['address']}:{db_config['port']}/"
        )
        self.db = sessionmaker(bind=engine)()
        self.db.query(Module).filter(Module.token == TEST_MODULE_TOKEN).delete()
        self.db.add(Module(token=TEST_MODULE_TOKEN, name="_pytest_heartbeat_module", fqdn=TEST_MODULE_FQDN))
        self.db.commit()

    def tearDown(self):
        self.client.disconnect()
        self.db.query(Module).filter(Module.token == TEST_MODULE_TOKEN).delete()
        self.db.commit()
        self.db.close()

    def test_ping_server(self):
        # Ask server ping
        self.client.emit('ping_server')

        # Waiting for response
        response = self.client.get_received()

        # Si le timestamps est un float c'est bon
        self.assertIsInstance(response[0]['args'][0]['timestamp'], float, "Error: 'timestamp' must be a float!")

    def test_hearbeat(self):
        # define HeartBeat Data
        data_to_send = {"date": time(), "fqdn": TEST_MODULE_FQDN, "token": TEST_MODULE_TOKEN}

        self.client.emit("heartbeat", data_to_send)

        response = self.client.get_received()
        self.assertEqual(response[0]['name'], 'response-heartbeat', "Error: expected a successful heartbeat response!")
        self.assertIn('receive-at', response[0]['args'][0])
