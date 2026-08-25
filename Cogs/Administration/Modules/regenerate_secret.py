from secrets import token_urlsafe
from argon2 import PasswordHasher
from flask import request, redirect, url_for, render_template

from Utils.verify_login import verify_login
from Utils.Database.user import User
from Utils.Database.permission import Permission
from Utils.Database.modules import Module


def regenerate_secret_cogs(database):
    if verify_login(database) and verify_login(database) != 'desactivated':
        user_data = database.query(User).filter(User.token == request.cookies.get('token')).first()
        user_permission = database.query(Permission).filter(Permission.user_token == request.cookies.get('token')).first()

        if not user_permission.admin:  # Action sensible : réservée aux admins
            return redirect(url_for('home'))

        module = database.query(Module).filter(Module.token == request.form["module_token"]).first()
        if module is None:
            return redirect(url_for('show_modules'))

        plain_secret = token_urlsafe(32)
        module.client_secret = PasswordHasher().hash(plain_secret)
        database.commit()

        return render_template('Administration/modules/client_secret_shown.html',
                               module=module, plain_secret=plain_secret,
                               user_permission=user_permission, user_data=user_data)

    elif verify_login(database) == 'desactivated':
        return redirect(url_for('sso_login', error='2'))
    else:
        return redirect(url_for('sso_login'))
