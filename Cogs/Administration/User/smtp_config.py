from Utils.verify_login import verify_login
from flask import redirect, url_for, request, render_template

from Utils.Database.user import User
from Utils.Database.permission import Permission
from Utils.Database.modules import Module
from Utils.Database.config import Config


def smtp_config_cogs(database):
    if verify_login(database) and verify_login(database) != 'desactivated':
        # On récupère les modules afin de pouvoir faire une redirection sur la page via la sidebar
        modules_info = database.query(Module).all()

        # On récupère les données de l'utilisateur afin de pouvoir l'afficher
        user_data = database.query(User).filter(User.token == request.cookies.get('token')).first()

        # On récupère les permissions de l'utilisateur afin de pouvoir afficher les options qui correspondent
        user_permission = database.query(Permission).filter(Permission.user_token == request.cookies.get('token')).first()

        if not user_permission.edit_smtp_config and not user_permission.admin:  # Si l'utilisateur n'a pas la permission, redirection vers la page d'accueil
            return redirect(url_for('home'))

        if request.method == 'POST':
            for element in request.form:
                database.query(Config).filter(Config.name == element).update({"content": request.form[element]})
                database.commit()

            return redirect(url_for('smtp_config'))
        else:
            smtp_info = database.query(Config).filter(
                Config.name.in_([
                    "SMTP_URL", "SMTP_PORT", "SMTP_EMAIL", "SMTP_PASSWORD",
                    "MAIL_VERIFICATION_SUJET", "MAIL_VERIFICATION_CONTENU"
                ])
            ).all()
            return render_template('Administration/smtp_config.html', smtp_info=smtp_info,
                                   user_permission=user_permission, modules_info=modules_info, user_data=user_data)
    elif verify_login(database) == 'desactivated':
        return redirect(url_for('sso_login', error='2'))
    else:
        return redirect(url_for('sso_login'))
