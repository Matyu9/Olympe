from Utils.verify_login import verify_login
from flask import redirect, url_for, request
from json import dump

from Utils.Database.permission import Permission
from Utils.Database.modules import Module

import app


def maintenance_cogs(database):
    if verify_login(database) and verify_login(database) != 'desactivated':
        # On récupère les permissions de l'utilisateur afin de pouvoir afficher les options qui correspondent
        user_permission = database.query(Permission).filter(Permission.user_token == request.cookies.get('token')).first()

        if not user_permission.on_off_maintenance and not user_permission.admin:  # Si l'utilisateur n'a pas la permission, redirection vers la page d'accueil
            return redirect(url_for('home'))

        if request.method == 'POST':
            if request.form["module_name"] == app.config_data['modules'][0]['name']: # Si c'est Olympe qui est en maintenance,
                app.config_data['modules'][0]['maintenance'] = not app.config_data['modules'][0]['maintenance'] # On enregistre dans le fichier json du module

                with open(app.file_path, 'w') as file:
                    dump(app.config_data, file, indent=4)

                database.query(Module).filter(Module.token == request.form["module_token"]).update(
                    {
                        "maintenance": not app.config_data['modules'][0]['maintenance']
                    }
                )

            else:
                database.query(Module).filter(Module.token == request.form["module_token"]).update(
                    {"maintenance": ~Module.maintenance}  # Inverse la valeur booléenne
                )

            database.commit()

            return redirect(url_for('show_modules', module_token=request.form["module_token"]))

    elif verify_login(database) == 'desactivated':
        return redirect(url_for('sso_login', error='2'))
    else:
        return redirect(url_for('sso_login'))
