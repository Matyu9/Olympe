from flask import request
from Utils.Database.user import User
from Utils.Database.config import Config



def api_user_info_cogs(database, error):
    status_code = 200
    credentials_status = False
    unique_id = ""
    secret_id = ""
    username = request.json['username']  # Sauvegarde du nom d'utilisateur
    password = request.json['password']  # Sauvegarde du mot de passe

    # Séléction des données requises pour valider la connexion.
    row = database.query(User).filter(User.username == username).first()

    validation_code = database.query(Config.content).filter(Config.name == "secret_token").scalar()


    json_to_send = {
        "status_code": status_code,
        "credentials_status": credentials_status,
        "unique_id": unique_id,
        "secret_id": secret_id
    }
    print(jsonify(json_to_send))
    return jsonify(json_to_send)