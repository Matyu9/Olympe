from Utils.verify_login import verify_login
from flask import redirect, url_for, request, render_template

from Utils.Database.user import User
from Utils.Database.permission import Permission
from Utils.Database.modules import Module
from Utils.Database.config import Config, set_config

SMTP_KEYS = ["SMTP_URL", "SMTP_PORT", "SMTP_EMAIL", "SMTP_PASSWORD",
             "MAIL_VERIFICATION_SUJET", "MAIL_VERIFICATION_CONTENU"]


def _get_smtp_info(database):
    # Renvoie toujours les 6 clés dans le même ordre, avec un contenu vide tant qu'elles ne sont pas configurées
    rows = {row.name: row for row in database.query(Config).filter(Config.name.in_(SMTP_KEYS)).all()}
    return [rows.get(key) or Config(name=key, content="") for key in SMTP_KEYS]


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
                set_config(database, element, request.form[element])
            database.commit()

            return redirect(url_for('smtp_config'))
        else:
            smtp_info = _get_smtp_info(database)
            return render_template('Administration/smtp_config.html', smtp_info=smtp_info,
                                   user_permission=user_permission, modules_info=modules_info, user_data=user_data)
    elif verify_login(database) == 'desactivated':
        return redirect(url_for('sso_login', error='2'))
    else:
        return redirect(url_for('sso_login'))
