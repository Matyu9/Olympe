from Utils.verify_login import login_required
from flask import request, render_template

from Utils.Database.user import User
from Utils.Database.permission import Permission


@login_required(permission='add_modules')
def show_install_form_cogs(database):
    user_data = database.query(User).filter(User.token == request.cookies.get('token')).first()
    user_permission = database.query(Permission).filter(Permission.user_token == request.cookies.get('token')).first()

    return render_template('Administration/modules/install_module.html',
                           user_permission=user_permission, user_data=user_data)
