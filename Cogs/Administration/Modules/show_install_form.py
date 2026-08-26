from Utils.verify_login import verify_login
from flask import redirect, url_for, request, render_template

from Utils.Database.user import User
from Utils.Database.permission import Permission


def show_install_form_cogs(database):
    if verify_login(database) and verify_login(database) != 'desactivated':
        user_data = database.query(User).filter(User.token == request.cookies.get('token')).first()
        user_permission = database.query(Permission).filter(Permission.user_token == request.cookies.get('token')).first()

        if not user_permission.add_modules and not user_permission.admin:
            return redirect(url_for('home'))

        return render_template('Administration/modules/install_module.html',
                               user_permission=user_permission, user_data=user_data)

    elif verify_login(database) == 'desactivated':
        return redirect(url_for('sso_login', error='2'))
    else:
        return redirect(url_for('sso_login'))
