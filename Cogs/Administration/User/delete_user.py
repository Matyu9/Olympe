from Utils.verify_login import verify_login
from flask import redirect, url_for, request

from Utils.Database.permission import Permission
from Utils.Database.user import User


def delete_user_cogs(database):
    # Vérification de si l'utilisateur est bien connecté et n'a pas un compte désactivé
    if verify_login(database) and verify_login(database) != 'desactivated':
        # Si l'utilisateur n'a pas les permissions, redirection vers la page d'accueil
        user_permission = database.query(Permission).filter(Permission.user_token == request.cookies.get('token')).first()

        if not user_permission.delete_account and not user_permission.admin:
            return redirect(url_for('show_user'))

        # Suppressions des permissions et des données de l'utilisateur.
        database.query(Permission).filter(Permission.user_token == request.form["token_to_delete"]).delete()
        database.query(User).filter(User.token == request.form["token_to_delete"]).delete()
        database.commit()

        return redirect(url_for('show_user'))

    elif verify_login(database) == "desactivated":
        return redirect(url_for('sso_login', error='2'))
    else:
        return redirect(url_for('sso_login'))
