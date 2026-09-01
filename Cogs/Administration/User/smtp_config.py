from Utils.verify_login import login_required
from flask import redirect, url_for, request, render_template

from Utils.Database.user import User
from Utils.Database.config import Config, set_config
from Utils.Administration.Modules.module_access import visible_modules_for_user
from Utils.permission_resolution import get_effective_permission_view

SMTP_KEYS = ["SMTP_URL", "SMTP_PORT", "SMTP_EMAIL", "SMTP_PASSWORD",
             "MAIL_VERIFICATION_SUJET", "MAIL_VERIFICATION_CONTENU"]


def _get_smtp_info(database):
    # Renvoie toujours les 6 clés dans le même ordre, avec un contenu vide tant qu'elles ne sont pas configurées
    rows = {row.name: row for row in database.query(Config).filter(Config.name.in_(SMTP_KEYS)).all()}
    return [rows.get(key) or Config(name=key, content="") for key in SMTP_KEYS]


@login_required(permission='edit_smtp_config')
def smtp_config_cogs(database):
    # On récupère les données de l'utilisateur afin de pouvoir l'afficher
    user_data = database.query(User).filter(User.token == request.cookies.get('token')).first()

    # On récupère les modules afin de pouvoir faire une redirection sur la page via la sidebar
    modules_info = visible_modules_for_user(database, user_data)

    # On récupère les permissions effectives de l'utilisateur (droit personnel éventuellement forcé
    # par un groupe, cf. Utils/permission_resolution.py)
    user_permission = get_effective_permission_view(database, request.cookies.get('token'))

    if request.method == 'POST':
        # Whitelist stricte : évite qu'un champ de formulaire arbitraire (ex: secret_token,
        # une clé de chiffrement) puisse écraser une entrée de config sensible.
        for element in request.form:
            if element in SMTP_KEYS:
                set_config(database, element, request.form[element])
        database.commit()

        return redirect(url_for('admin.smtp_config'))
    else:
        smtp_info = _get_smtp_info(database)
        return render_template('Administration/smtp_config.html', smtp_info=smtp_info,
                               user_permission=user_permission, modules_info=modules_info, user_data=user_data)
