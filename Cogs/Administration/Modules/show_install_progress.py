from Utils.verify_login import verify_login
from flask import redirect, url_for, request, render_template

from Utils.Database.user import User
from Utils.Database.permission import Permission
from Utils.Database.module_installation import ModuleInstallation


def show_install_progress_cogs(database, installation_id):
    if verify_login(database) and verify_login(database) != 'desactivated':
        user_data = database.query(User).filter(User.token == request.cookies.get('token')).first()
        user_permission = database.query(Permission).filter(Permission.user_token == request.cookies.get('token')).first()

        if not user_permission.add_modules and not user_permission.admin:
            return redirect(url_for('home'))

        installation = database.query(ModuleInstallation).filter(ModuleInstallation.id == installation_id).first()
        if installation is None:
            return redirect(url_for('show_modules'))

        return render_template('Administration/modules/install_progress.html',
                               installation=installation,
                               user_permission=user_permission, user_data=user_data)

    elif verify_login(database) == 'desactivated':
        return redirect(url_for('sso_login', error='2'))
    else:
        return redirect(url_for('sso_login'))
