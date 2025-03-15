from uuid import uuid3, uuid1
from Utils.verify_login import verify_login
from flask import redirect, url_for, request, render_template

from Utils.Database.user import User
from Utils.Database.permission import Permission
from Utils.Database.modules import Module


def add_modules_cogs(database):
    if verify_login(database) and verify_login(database) != 'desactivated':
        # On récupère les modules afin de pouvoir faire une redirection sur la page via la sidebar
        modules_info = database.query(Module).all()

        # On récupère les données de l'utilisateur afin de pouvoir l'afficher
        user_data = database.query(User).filter(User.token == request.cookies.get('token')).first()

        # On récupère les permissions de l'utilisateur afin de pouvoir afficher les options qui correspondent
        user_permission = database.query(Permission).filter(Permission.user_token == request.cookies.get('token')).first()

        if not user_permission.add_modules and not user_permission.admin:  # Si l'utilisateur n'as pas la permission, redirection vers la page d'accueil
            return redirect(url_for('home'))

        if request.method == 'GET':
            # return render_template('Administration/disabled_feature.html')
            return render_template('Administration/modules/add_modules.html', user_permission=user_permission, user_data=user_data)
        elif request.method == 'POST':
            token = str(uuid3(uuid1(), str(uuid1())))  # Génération d'un token unique
            try:
                _maintenance = 1 if request.form["module_maintenance"] else 0
            except Exception as e:
                print(e)
                _maintenance = 0

            database.add(
                Module(
                    token=token,
                    name=request.form["module_name"],
                    fqdn=request.form["module_fqdn"],
                    maintenance = bool(_maintenance)
                )
            )
            database.commit()

            return redirect(url_for('show_modules', module_token=token))

    elif verify_login(database) == 'desactivated':
        return redirect(url_for('sso_login', error='2'))
    else:
        return redirect(url_for('sso_login'))
