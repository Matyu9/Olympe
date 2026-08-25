from flask import request, redirect, url_for, render_template
from Utils.verify_login import verify_login
from Utils.Administration.User.check_global_permission_edit import check_perm

from Utils.Database.config import Config, get_config, set_config
from Utils.Database.user import User
from Utils.Database.permission import Permission
from Utils.Database.modules import Module

# Clé de réglage (table Config) -> attribut correspondant sur le modèle Permission
PERMISSION_KEYS = {
    'edit_username': 'edit_username',
    'edit_password': 'edit_password',
    'edit_email': 'edit_email',
    'edit_profile_picture': 'edit_profile_picture',
    'edit_a2f': 'edit_A2F',
}


def global_permission_cogs(database):
    if verify_login(database) and verify_login(database) != 'desactivated':
        # On récupère les modules afin de pouvoir faire une redirection sur la page via la sidebar
        modules_info = database.query(Module).all()

        # On récupère les données de l'utilisateur afin de pouvoir l'afficher
        user_data = database.query(User).filter(User.token == request.cookies.get('token')).first()

        # On récupère les permissions de l'utilisateur afin de pouvoir afficher les options qui correspondent
        user_permission = database.query(Permission).filter(Permission.user_token == request.cookies.get('token')).first()

        # Valeurs par défaut à "0" tant qu'aucun admin n'a encore sauvegardé de réglage
        permission = [get_config(database, key) for key in PERMISSION_KEYS]

        if not user_permission.allow_edit_username and not user_permission.allow_edit_email and not user_permission.allow_edit_password and not user_permission.allow_edit_profile_picture and not user_permission.allow_edit_A2F and not user_permission.admin:
            return redirect(url_for('home'))

        if request.method == 'POST': # Si la request est de type "POST" on met à jour les permission et on affiche les dernières valeurs
            for key, permission_attr in PERMISSION_KEYS.items():
                value = check_perm(key)
                database.query(Permission).update({permission_attr: value})
                set_config(database, key, value)
            database.commit()

            permission = [get_config(database, key) for key in PERMISSION_KEYS]


        return render_template('Administration/global_permission.html', permission=permission,
                               user_permission=user_permission, modules_info=modules_info, user_data=user_data)

    elif verify_login(database) == "desactivated":
        return redirect(url_for('sso_login', error='2'))
    else:
        return redirect(url_for('sso_login'))
