from Utils.Administration.User.create_user import create_user
from Utils.verify_login import verify_login
from flask import redirect, url_for, request, render_template

from Utils.Database.user import User
from Utils.Database.permission import Permission
from Utils.Database.modules import Module


def add_user_cogs(database):
    # Vérification de si l'utilisateur est bien connecté et n'a pas un compte désactivé
    if verify_login(database) and verify_login(database) != 'desactivated':
        # On récupère les modules afin de pouvoir faire une redirection sur la page via la sidebar
        modules_info = database.query(Module).all()

        # On récupère les données de l'utilisateur afin de pouvoir l'afficher
        user_data = database.query(User).filter(User.token == request.cookies.get('token')).first()

        # On récupère les permissions de l'utilisateur afin de pouvoir afficher les options qui correspondent
        user_permission = database.query(Permission).filter(Permission.user_token == request.cookies.get('token')).first()

        if not user_permission.create_user and not user_permission.admin:
            return redirect(url_for("home"))

        if request.method == 'POST':  # S'il fait une requete de type POST
            _create_user = create_user(database)  # Création de l'utilisateur
            return redirect(url_for('show_user', user_token=_create_user))
        elif request.method == 'GET':  # S'il fait une requete de type GET
            return render_template('Administration/add_user.html', modules_info=modules_info, user_data=user_data, user_permission=user_permission)

    elif verify_login(database) == "desactivated":
        return redirect(url_for('sso_login', error='2'))
    else:
        return redirect(url_for('sso_login'))
