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


def verify_A2F(A2F_secret):
    try:
        key = totp.TOTP(A2F_secret)
    except BadRequestKeyError:
        key = totp.TOTP(A2F_secret)

    return key.verify(request.form['a2f-code'].replace(" ", ""))
