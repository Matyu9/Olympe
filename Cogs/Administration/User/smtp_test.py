from Utils.verify_login import verify_login
from Utils.email_utils import send_test_email
from flask import redirect, url_for, request

from Utils.Database.permission import Permission


def smtp_test_cogs(database):
    if verify_login(database) and verify_login(database) != 'desactivated':
        # On récupère les permissions de l'utilisateur afin de pouvoir afficher les options qui correspondent
        user_permission = database.query(Permission).filter(Permission.user_token == request.cookies.get('token')).first()

        if not user_permission.edit_smtp_config and not user_permission.admin:  # Si l'utilisateur n'as pas la permission, redirection vers la page d'accueil
            return redirect(url_for('home'))

        if request.method == 'POST':
            send_test_email(database)
            return redirect(url_for('smtp_config'))
        else:
            return redirect(url_for('smtp_config'))
    elif verify_login(database) == 'desactivated':
        return redirect(url_for('sso_login', error='2'))
    else:
        return redirect(url_for('sso_login'))
