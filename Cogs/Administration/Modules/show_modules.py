from Utils.verify_login import login_required
from flask import redirect, url_for, request, render_template
from datetime import datetime

from Utils.Database.user import User
from Utils.Database.modules import Module
from Utils.Database.module_access import ModuleAccess
from Utils.Database.group import Group
from Utils.permission_resolution import get_effective_permission_view
from Utils.Administration.Modules.module_access import visible_modules_for_user, user_can_access_module


@login_required(permission='add_modules')
def show_modules_cogs(database):
    # On récupère les données de l'utilisateur afin de pouvoir l'afficher
    user_data = database.query(User).filter(User.token == request.cookies.get('token')).first()

    # 'add_modules' ("Ajouter un module") ne donne pas le droit de voir tous les modules
    # existants : cette console reste soumise à la même règle de visibilité que
    # l'accueil/la sidebar (modules non restreints + ceux couverts par show_all_modules/admin/accès
    # explicite, cf. Utils/Administration/Modules/module_access.py).
    modules_info = visible_modules_for_user(database, user_data)

    # On récupère les permissions effectives de l'utilisateur (droit personnel éventuellement forcé
    # par un groupe, cf. Utils/permission_resolution.py)
    user_permission = get_effective_permission_view(database, request.cookies.get('token'))

    if request.method == 'POST':
        target_module = database.query(Module).filter(Module.token == request.form["token"]).first()
        if target_module is None or not user_can_access_module(database, user_data, target_module):
            return redirect(url_for('admin.show_modules'))

        database.query(Module).filter(Module.token == request.form["token"]).update(
            {
                "name": request.form["module_name"],
                "fqdn": request.form["module_url"],
                "socket_url": request.form["socket_url"],
                "require_consent": bool(request.form.get("module_require_consent"))
            }
        )
        database.commit()

        return redirect(url_for('admin.show_modules', module_token=request.form["token"]))
    else:
        if request.args.get('module_token'):
            selected_module_info = database.query(Module).filter(Module.token == request.args.get('module_token')).first()
            if selected_module_info is None or not user_can_access_module(database, user_data, selected_module_info):
                return redirect(url_for('admin.show_modules'))


            time_diff = datetime.now() - datetime.fromtimestamp(selected_module_info.last_heartbeat)

            date = [datetime.fromtimestamp(selected_module_info.last_heartbeat).strftime("%H:%M:%S - %d/%m/%Y"),
                    [int(time_diff.days),
                     int(time_diff.seconds // 3600),
                     int((time_diff.seconds% 3600) // 60),
                     int(time_diff.seconds % 60)
                     ]
                    ]

            # Accès restreint : on résout chaque ligne ModuleAccess en username/nom de groupe
            # pour l'affichage (pas de jointure ORM dans ce codebase, cf. Permission)
            access_rows = database.query(ModuleAccess).filter(ModuleAccess.module_id == selected_module_info.id).all()
            module_user_access = []
            module_group_access = []
            for access_row in access_rows:
                if access_row.user_token:
                    access_user = database.query(User).filter(User.token == access_row.user_token).first()
                    if access_user:
                        module_user_access.append({"access_id": access_row.id, "username": access_user.username})
                elif access_row.group_id:
                    access_group = database.query(Group).filter(Group.id == access_row.group_id).first()
                    if access_group:
                        module_group_access.append({"access_id": access_row.id, "group_id": access_group.id, "group_name": access_group.name})
            # Seuls les groupes/utilisateurs pas encore autorisés apparaissent dans les sélecteurs d'ajout
            already_granted_group_ids = {access["group_id"] for access in module_group_access}
            available_groups = [group for group in database.query(Group).all() if group.id not in already_granted_group_ids]
            already_granted_usernames = {access["username"] for access in module_user_access}
            all_usernames = [user.username for user in database.query(User).all() if user.username not in already_granted_usernames]

            return render_template('Administration/show_one_modules.html',
                                   selected_module_info=selected_module_info, modules_info=modules_info,
                                   user_permission=user_permission, user_data=user_data, date=date,
                                   module_user_access=module_user_access, module_group_access=module_group_access,
                                   all_groups=available_groups, all_usernames=all_usernames)
        else:
            return render_template('Administration/show_modules.html', modules_info=modules_info,
                               user_permission=user_permission, user_data=user_data)
