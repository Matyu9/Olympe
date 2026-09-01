from flask import request, redirect, url_for, render_template
from Utils.verify_login import login_required
from Utils.Administration.User.check_global_permission_edit import check_perm

from Utils.Database.config import get_config, set_config
from Utils.Database.user import User
from Utils.Database.permission import Permission
from Utils.Administration.Modules.module_access import visible_modules_for_user
from Utils.permission_resolution import get_effective_permission_view

# Clé de réglage (table Config) -> attribut correspondant sur le modèle Permission
PERMISSION_KEYS = {
    'edit_username': 'edit_username',
    'edit_password': 'edit_password',
    'edit_email': 'edit_email',
    'edit_profile_picture': 'edit_profile_picture',
    'edit_a2f': 'edit_A2F',
}


def _can_edit_global_permissions(effective):
    return (
        effective('allow_edit_username') or effective('allow_edit_email')
        or effective('allow_edit_password') or effective('allow_edit_profile_picture')
        or effective('allow_edit_A2F') or effective('admin')
    )


@login_required(permission=_can_edit_global_permissions)
def global_permission_cogs(database):
    # On récupère les données de l'utilisateur afin de pouvoir l'afficher
    user_data = database.query(User).filter(User.token == request.cookies.get('token')).first()

    # On récupère les modules afin de pouvoir faire une redirection sur la page via la sidebar
    modules_info = visible_modules_for_user(database, user_data)

    # On récupère les permissions effectives de l'utilisateur (droit personnel éventuellement forcé
    # par un groupe, cf. Utils/permission_resolution.py)
    user_permission = get_effective_permission_view(database, request.cookies.get('token'))

    # Valeurs par défaut à "0" tant qu'aucun admin n'a encore sauvegardé de réglage
    permission = [get_config(database, key) for key in PERMISSION_KEYS]

    if request.method == 'POST': # Si la request est de type "POST" on met à jour les permission et on affiche les dernières valeurs
        for key, permission_attr in PERMISSION_KEYS.items():
            value = check_perm(key)
            database.query(Permission).update({permission_attr: value})
            set_config(database, key, value)
        database.commit()

        permission = [get_config(database, key) for key in PERMISSION_KEYS]

    return render_template('Administration/global_permission.html', permission=permission,
                           user_permission=user_permission, modules_info=modules_info, user_data=user_data)
