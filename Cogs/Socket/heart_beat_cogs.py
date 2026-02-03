from flask_socketio import emit
from time import time

from Utils.Database.modules import Module

def heart_beat_cogs(data, database):
    fqdn_data = database.query(Module).filter(Module.token == data["token"]).first()
    server_time = round(time())
    saved_time = round((data['date']+server_time)/2)

    if fqdn_data.fqdn == data["fqdn"] and fqdn_data.token == data["token"]:
        database.query(Module).filter(Module.token == data["token"]).update({
            "last_heartbeat": saved_time,
            "status": True
        })
        database.commit()

        emit('response-heartbeat', {"receive-at": saved_time})
    else:
        emit('error-response', {"message": "token or FQDN invalid"})
