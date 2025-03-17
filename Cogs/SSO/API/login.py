from flask import request, jsonify
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from werkzeug.exceptions import BadRequestKeyError
from Utils.verify_login import verify_A2F

from Utils.Database.user import User
from Utils.Database.config import Config


def api_login_cogs(database, error):
    status_code = 200
    credentials_status = False
    unique_id = ""
    secret_id = ""
    username = request.json['username']  # Sauvegarde du nom d'utilisateur
    password = request.json['password']  # Sauvegarde du mot de passe

    # Séléction des données requises pour valider la connexion.
    row = database.query(User).filter(User.username == username).first()

    validation_code = database.query(Config.content).filter(Config.name == "secret_token").scalar()

    try:
        dfa_code = request.json['dfa_code']  # Sauvegarde du code d'A2F si l'utilisateur en a rempli un
    except BadRequestKeyError:
        dfa_code = None

    if row is None:  # Si aucune correspondance, redirect vers la page de login avec le message d'erreur n°1
        status_code = 401

    try:
        PasswordHasher().verify(row.password, password)  # Verification de la correspondance du MDP

        if row.A2F and dfa_code is None or row.A2F and not dfa_code:
            # Si l'A2F est activé, mais qu'aucun code n'est fournis
            status_code = 418
        elif not row.A2F or verify_A2F(row.A2F_secret):  # Si l'A2F n'est pas activé ou que le code est correcte
            credentials_status = True
            unique_id = row.token
            secret_id = validation_code
        else:  # Dans tous les autres cas
            status_code = 401

    except VerifyMismatchError:  # Si le MDP ne correspond pas, redirect vers le login avec le message d'erreur n°1
        status_code = 401
    except TypeError:
        status_code = 401

    json_to_send = {
        "status_code": status_code,
        "credentials_status": credentials_status,
        "unique_id": unique_id,
        "secret_id": secret_id
    }
    print(jsonify(json_to_send))
    return jsonify(json_to_send)

