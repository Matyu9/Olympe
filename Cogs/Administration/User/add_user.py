from Utils.Administration.User.create_user import create_user
from Utils.verify_login import login_required
from flask import redirect, url_for, request, render_template

from Utils.Database.user import User
from Utils.Database.permission import Permission
from Utils.Administration.Modules.module_access import visible_modules_for_user


@login_required(permission='create_user')
def add_user_cogs(database):
    # On récupère les données de l'utilisateur afin de pouvoir l'afficher
    user_data = database.query(User).filter(User.token == request.cookies.get('token')).first()

    # On récupère les modules afin de pouvoir faire une redirection sur la page via la sidebar
    modules_info = visible_modules_for_user(database, user_data)

    # On récupère les permissions de l'utilisateur afin de pouvoir afficher les options qui correspondent
    user_permission = database.query(Permission).filter(Permission.user_token == request.cookies.get('token')).first()

    if request.method == 'POST':  # S'il fait une requete de type POST
        _create_user = create_user(database)  # Création de l'utilisateur
        return redirect(url_for('show_user', user_token=_create_user))
    elif request.method == 'GET':  # S'il fait une requete de type GET
        return render_template('Administration/add_user.html', modules_info=modules_info, user_data=user_data, user_permission=user_permission)
