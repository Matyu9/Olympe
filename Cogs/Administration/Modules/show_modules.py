from Utils.verify_login import verify_login
from flask import redirect, url_for, request, render_template
from datetime import datetime

from Utils.Database.user import User
from Utils.Database.permission import Permission
from Utils.Database.modules import Module


def show_modules_cogs(database):
    if verify_login(database) and verify_login(database) != 'desactivated':
        # On récupère les modules afin de pouvoir faire une redirection sur la page via la sidebar
        modules_info = database.query(Module).all()

        # On récupère les données de l'utilisateur afin de pouvoir l'afficher
        user_data = database.query(User).filter(User.token == request.cookies.get('token')).first()

        # On récupère les permissions de l'utilisateur afin de pouvoir afficher les options qui correspondent
        user_permission = database.query(Permission).filter(Permission.user_token == request.cookies.get('token')).first()

        if not user_permission.add_modules and not user_permission.admin:  # Si l'utilisateur n'a pas la permission, redirection vers la page d'accueil
            return redirect(url_for('home'))

        if request.method == 'POST':
            database.query(Module).filter(Module.token == request.form["token"]).update(
                {
                    "name": request.form["module_name"],
                    "fqdn": request.form["module_url"],
                    "socket_url": request.form["socket_url"]
                }
            )
            database.commit()

            return redirect(url_for('show_modules', module_token=request.form["token"]))
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

                return render_template('Administration/show_one_modules.html',
                                       selected_module_info=selected_module_info, modules_info=modules_info,
                                       user_permission=user_permission, user_data=user_data, date=date)
            else:
                return render_template('Administration/show_modules.html', modules_info=modules_info,
                                   user_permission=user_permission, user_data=user_data)

    elif verify_login(database) == 'desactivated':
        return redirect(url_for('sso_login', error='2'))
    else:
        return redirect(url_for('sso_login'))
