from datetime import datetime
from Utils.verify_login import login_required
from flask import request, render_template

from sqlalchemy import func
from Utils.Database.user import User
from Utils.Administration.Modules.module_access import visible_modules_for_user
from Utils.permission_resolution import get_effective_permission_view


def _greeting():
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Bonjour"
    if 12 <= hour < 18:
        return "Bon après-midi"
    return "Bonsoir"


@login_required(desactivated_redirect='olympe_fqdn')
def user_home_cogs(database):
    # Récupération des données de l'utilisateur
    user_information = database.query(User).filter(User.token == request.cookies.get('token')).first()

    if request.method == 'GET':
        # Récupération des permissions effectives de l'utilisateur (droit personnel éventuellement
        # forcé par un groupe, cf. Utils/permission_resolution.py)
        user_permission = get_effective_permission_view(database, request.cookies.get('token'))
        modules_info = visible_modules_for_user(database, user_information)
        nb_user = database.query(func.count(User.id)).scalar()
        nb_module = len(modules_info)
        nb_module_online = sum(1 for module in modules_info if module.status and not module.maintenance)

        return render_template('User/index.html', user_information=user_information,
                               user_permission=user_permission, modules_info=modules_info, nb_user=nb_user,
                               nb_module=nb_module, nb_module_online=nb_module_online, greeting=_greeting())

    else:
        return None
