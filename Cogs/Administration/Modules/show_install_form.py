from Utils.verify_login import login_required
from flask import request, render_template

from Utils.Database.user import User
from Utils.permission_resolution import get_effective_permission_view


@login_required(permission='add_modules')
def show_install_form_cogs(database):
    user_data = database.query(User).filter(User.token == request.cookies.get('token')).first()
    user_permission = get_effective_permission_view(database, request.cookies.get('token'))

    return render_template('Administration/modules/install_module.html',
                           user_permission=user_permission, user_data=user_data)
