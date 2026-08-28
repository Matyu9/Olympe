from functools import wraps

from flask import request, redirect, url_for
from pyotp import totp
from werkzeug.exceptions import BadRequestKeyError

from Utils.Database.user import User
from Utils.Database.config import Config
from Utils.Database.permission import Permission
from Utils.Database.modules import Module

def verify_login(database):
    token = request.cookies.get('token')
    try:
        if database.query(User.desactivated).filter(User.token == token).scalar():
            return "desactivated"
    except TypeError:
        return False

    token_validation = database.query(User.id).filter(User.token == token).scalar()
    validation = request.cookies.get('validation')
    validation_from_db = database.query(Config.content).filter(Config.name == "secret_token").scalar()

    return True if token_validation is not None and validation == validation_from_db else False


def verify_A2F(A2F_secret):
    try:
        key = totp.TOTP(A2F_secret)
    except BadRequestKeyError:
        key = totp.TOTP(A2F_secret)

    try: # Utilisation classique via le formulaire
        return key.verify(request.form['a2f-code'].replace(" ", ""))
    except BadRequestKeyError: # Sinon utilisation de l'API
        return key.verify(request.json['dfa_code'].replace(" ", ""))


def login_required(permission=None, redirect_endpoint='home', desactivated_redirect='default'):
    """Factorise le bloc de garde duplique dans la plupart des cogs :
        if verify_login(database) and verify_login(database) != 'desactivated':
            ...
        elif verify_login(database) == 'desactivated':
            return redirect(url_for('sso_login', error='2'))
        else:
            return redirect(url_for('sso_login'))

    `permission` : nom d'attribut booleen de `Permission` requis (le bypass `admin` s'applique
    toujours en plus), ou une fonction `user_permission -> bool` pour les permissions combinees
    (ex: `_can_manage_groups` dans edit_group_members.py). `None` ne verifie que la connexion.
    `redirect_endpoint` : endpoint Flask vers lequel rediriger si la permission manque.
    `desactivated_redirect` : 'default' redirige vers sso_login (comportement des pages
    d'administration) ; 'olympe_fqdn' redirige vers le fqdn du module "olympe" en base
    (comportement historique des pages Cogs/User/*, qui restent joignables via d'autres domaines).

    Le cogs decore continue de recevoir `database` en premier argument (signature inchangee cote
    app.py) et garde la responsabilite de re-recuperer `user_permission`/`user_data` pour l'affichage
    si besoin : ce decorateur ne fait que la garde, pas l'injection de donnees.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(database, *args, **kwargs):
            login_state = verify_login(database)

            if not login_state:
                return redirect(url_for('sso_login', error='0'))

            if login_state == 'desactivated':
                if desactivated_redirect == 'olympe_fqdn':
                    olympe_module = database.query(Module.fqdn).filter(Module.name == "olympe").first()
                    # Si la ligne "olympe" n'existe pas (ou plus) en base, ne pas planter en 500 :
                    # retomber sur la redirection par defaut plutot que de crasher sur `.fqdn`.
                    if olympe_module is not None:
                        return redirect(olympe_module.fqdn + '/sso/login/?error=2')
                return redirect(url_for('sso_login', error='2'))

            if permission is not None:
                user_permission = database.query(Permission).filter(
                    Permission.user_token == request.cookies.get('token')
                ).first()
                allowed = permission(user_permission) if callable(permission) else (
                    getattr(user_permission, permission) or user_permission.admin
                )
                if not allowed:
                    return redirect(url_for(redirect_endpoint))

            return view_func(database, *args, **kwargs)
        return wrapped
    return decorator