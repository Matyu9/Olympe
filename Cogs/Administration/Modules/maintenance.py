from Utils.verify_login import login_required
from flask import redirect, url_for, request, current_app
from json import dump

from Utils.Database.modules import Module


@login_required(permission='on_off_maintenance')
def maintenance_cogs(database):
    if request.method == 'POST':
        config_data = current_app.config['CONFIG_DATA']
        if request.form["module_name"] == config_data['modules'][0]['name']: # Si c'est Olympe qui est en maintenance,
            config_data['modules'][0]['maintenance'] = not config_data['modules'][0]['maintenance'] # On enregistre dans le fichier json du module

            with open(current_app.config['CONFIG_FILE_PATH'], 'w') as file:
                dump(config_data, file, indent=4)

            database.query(Module).filter(Module.token == request.form["module_token"]).update(
                {
                    "maintenance": not config_data['modules'][0]['maintenance']
                }
            )

        else:
            database.query(Module).filter(Module.token == request.form["module_token"]).update(
                {"maintenance": ~Module.maintenance}  # Inverse la valeur booléenne
            )

        database.commit()

        return redirect(url_for('admin.show_modules', module_token=request.form["module_token"]))
