from Utils.verify_login import login_required
from flask import redirect, url_for, request, render_template
from datetime import datetime

from Utils.Database.user import User
from Utils.Database.permission import Permission
from Utils.Database.modules import Module
from Utils.Database.module_access import ModuleAccess
from Utils.Database.group import Group


@login_required(permission='add_modules')
def show_modules_cogs(database):
    # Cette page est la console d'administration des modules : elle doit lister TOUS les
    # modules (y compris restreints) à l'admin, indépendamment de son accès personnel.
    modules_info = database.query(Module).all()

    # On récupère les données de l'utilisateur afin de pouvoir l'afficher
    user_data = database.query(User).filter(User.token == request.cookies.get('token')).first()

    # On récupère les permissions de l'utilisateur afin de pouvoir afficher les options qui correspondent
    user_permission = database.query(Permission).filter(Permission.user_token == request.cookies.get('token')).first()

    if request.method == 'POST':
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
