from Utils.verify_login import verify_login
from flask import redirect, url_for, request, render_template

from sqlalchemy import func
from Utils.Database.user import User
from Utils.Database.permission import Permission
from Utils.Database.modules import Module


def user_home_cogs(database):
    # Verification si l'utilisateur est connecté
    if not verify_login(database):
        return redirect(url_for('sso_login', error='0'))
    elif verify_login(database) == 'desactivated':  # Si l'utilisateur est connecté, mais que son compte est désactivé
        login_url = database.query(Module.fqdn).filter(Module.name == "olympe").first().fqdn
        return redirect(login_url+'/sso/login/?error=2')

    # Récupération des données de l'utilisateur
    user_information = database.query(User).filter(User.token == request.cookies.get('token')).first()

    if request.method == 'GET':
        # Récupération des permissions de l'utilisateur
        user_permission = database.query(Permission).filter(Permission.user_token == request.cookies.get('token')).first()
        modules_info = database.query(Module).all()
        nb_user = database.query(func.count(User.id)).scalar()
        nb_module = database.query(func.count(Module.id)).scalar()

        return render_template('User/index.html', user_information=user_information,
                               user_permission=user_permission, modules_info=modules_info, nb_user=nb_user, nb_module=nb_module)
