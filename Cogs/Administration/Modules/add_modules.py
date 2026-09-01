from uuid import uuid3, uuid1
from secrets import token_urlsafe
from argon2 import PasswordHasher
from Utils.verify_login import login_required
from flask import redirect, url_for, request, render_template

from Utils.Database.user import User
from Utils.Database.modules import Module
from Utils.permission_resolution import get_effective_permission_view


@login_required(permission='add_modules')
def add_modules_cogs(database):
    # On récupère les données de l'utilisateur afin de pouvoir l'afficher
    user_data = database.query(User).filter(User.token == request.cookies.get('token')).first()

    # On récupère les permissions effectives de l'utilisateur (droit personnel éventuellement forcé
    # par un groupe, cf. Utils/permission_resolution.py)
    user_permission = get_effective_permission_view(database, request.cookies.get('token'))

    if request.method == 'GET':
        # return render_template('Administration/disabled_feature.html')
        return render_template('Administration/modules/add_modules.html', user_permission=user_permission, user_data=user_data)
    elif request.method == 'POST':
        token = str(uuid3(uuid1(), str(uuid1())))  # Génération d'un token unique (= client_id OIDC)
        try:
            _maintenance = 1 if request.form["module_maintenance"] else 0
        except Exception as e:
            print(e)
            _maintenance = 0
        require_consent = bool(request.form.get("module_require_consent"))

        plain_secret = token_urlsafe(32)  # Secret client OIDC, affiché en clair une seule fois

        module = Module(
            token=token,
            name=request.form["module_name"],
            fqdn=request.form["module_fqdn"],
            maintenance=bool(_maintenance),
            require_consent=require_consent,
            client_secret=PasswordHasher().hash(plain_secret),
        )
        database.add(module)
        database.commit()

        return render_template('Administration/modules/client_secret_shown.html',
                               module=module, plain_secret=plain_secret,
                               user_permission=user_permission, user_data=user_data)
