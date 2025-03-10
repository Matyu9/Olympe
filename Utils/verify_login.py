from flask import request, redirect
from pyotp import totp
from werkzeug.exceptions import BadRequestKeyError

from Utils.Database.user import User
from Utils.Database.config import Config

def verify_login(database):
    token = request.cookies.get('token')
    try:
        if database.query(User.desactivated).filter(User.token == token).scalar():
            return "desactivated"
    except TypeError:
        return False

    token_validation = database.query(User.id).filter(User.token == token).scalar()
    validation = request.cookies.get('validation')
    validation_from_db = database.query(Config.content).filter(Config.name == "secret_token").scalar()

    return True if token_validation is not None and validation == validation_from_db[0] else False


def verify_A2F(database):
    try:
        key = totp.TOTP(database.select('''SELECT A2F_secret FROM cantina_administration.user WHERE username=%s''',
                                        (request.form['username']), number_of_data=1)[0])
    except BadRequestKeyError:
        key = totp.TOTP(database.select('''SELECT A2F_secret FROM cantina_administration.user WHERE token=%s''',
                                        (request.cookies.get('token')), number_of_data=1)[0])
    return key.verify(request.form['a2f-code'].replace(" ", ""))
