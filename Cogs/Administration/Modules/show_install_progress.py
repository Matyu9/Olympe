from Utils.verify_login import login_required
from flask import redirect, url_for, request, render_template

from Utils.Database.user import User
from Utils.Database.permission import Permission
from Utils.Database.module_installation import ModuleInstallation


@login_required(permission='add_modules')
def show_install_progress_cogs(database, installation_id):
    user_data = database.query(User).filter(User.token == request.cookies.get('token')).first()
    user_permission = database.query(Permission).filter(Permission.user_token == request.cookies.get('token')).first()

    installation = database.query(ModuleInstallation).filter(ModuleInstallation.id == installation_id).first()
    if installation is None:
        return redirect(url_for('show_modules'))

    return render_template('Administration/modules/install_progress.html',
                           installation=installation,
                           user_permission=user_permission, user_data=user_data)
