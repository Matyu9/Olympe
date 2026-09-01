from secrets import token_urlsafe
from argon2 import PasswordHasher
from flask import request, redirect, url_for, render_template

from Utils.verify_login import login_required
from Utils.Database.user import User
from Utils.Database.modules import Module
from Utils.permission_resolution import get_effective_permission_view


@login_required(permission='admin')  # Action sensible : réservée aux admins
def regenerate_secret_cogs(database):
    user_data = database.query(User).filter(User.token == request.cookies.get('token')).first()
    user_permission = get_effective_permission_view(database, request.cookies.get('token'))

    module = database.query(Module).filter(Module.token == request.form["module_token"]).first()
    if module is None:
        return redirect(url_for('admin.show_modules'))

    plain_secret = token_urlsafe(32)
    module.client_secret = PasswordHasher().hash(plain_secret)
    database.commit()

    return render_template('Administration/modules/client_secret_shown.html',
                           module=module, plain_secret=plain_secret,
                           user_permission=user_permission, user_data=user_data)
