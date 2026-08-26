from json import loads, dumps, JSONDecodeError
from time import time

from Utils.verify_login import verify_login
from flask import redirect, url_for, request, render_template

from Utils.Database.user import User
from Utils.Database.permission import Permission
from Utils.Database.module_installation import ModuleInstallation
from Utils.Administration.Modules.Installation.check_config_parameters import check_config_parameters, ModuleConfigValidationError
from Utils.Administration.Modules.Installation.credentials_crypto import encrypt_json
from Utils.Administration.Modules.Installation.installer import run_installation


def start_install_cogs(database, socketio, session_factory):
    if verify_login(database) and verify_login(database) != 'desactivated':
        user_data = database.query(User).filter(User.token == request.cookies.get('token')).first()
        user_permission = database.query(Permission).filter(Permission.user_token == request.cookies.get('token')).first()

        if not user_permission.add_modules and not user_permission.admin:
            return redirect(url_for('home'))

        if request.method != 'POST':
            return redirect(url_for('show_install_form'))

        try:
            config_file = loads(request.form['manifest_json'])
        except (JSONDecodeError, KeyError):
            return render_template('Administration/modules/install_module.html',
                                   user_permission=user_permission, user_data=user_data,
                                   errors=["Le manifeste JSON envoyé est invalide ou manquant."])

        try:
            check_config_parameters(config_file)
        except ModuleConfigValidationError as e:
            return render_template('Administration/modules/install_module.html',
                                   user_permission=user_permission, user_data=user_data,
                                   errors=e.errors)

        install_target = request.form.get('install_target', 'local')
        path_to_clone = request.form['path_to_clone']
        module_fqdn = request.form['module_fqdn']
        credentials_saved = bool(request.form.get('save_credentials'))

        ssh_config = None
        if install_target == 'remote':
            ssh_config = {
                'ssh-url': request.form['ssh_url'],
                'ssh-port': request.form['ssh_port'],
                'ssh-username': request.form['ssh_username'],
                'ssh-password': request.form['ssh_password'],
            }

        html_input_values = {}
        for key in config_file.get('configuration', {}).get('html-input', {}):
            html_input_values[key] = request.form.get(f'html_input__{key}', '')

        ssh_config_encrypted = None
        if install_target == 'remote' and credentials_saved:
            ssh_config_encrypted = encrypt_json(database, ssh_config)

        now = round(time())
        installation = ModuleInstallation(
            name=config_file['name'],
            url_repo=config_file['url-repo'],
            guidelines=config_file['guidelines'],
            beta=bool(config_file['beta']),
            install_script=config_file['configuration']['install-script'],
            html_input_schema=dumps(config_file['configuration']['html-input']),
            html_input_values=dumps(html_input_values),
            install_target=install_target,
            path_to_clone=path_to_clone,
            module_fqdn=module_fqdn,
            credentials_saved=credentials_saved,
            ssh_config_encrypted=ssh_config_encrypted,
            status='pending',
            created_at=now,
            updated_at=now,
        )
        database.add(installation)
        database.commit()

        install_params = {
            'install_target': install_target,
            'path_to_clone': path_to_clone,
            'module_fqdn': module_fqdn,
            'olympe_url': request.host_url.rstrip('/'),
            'ssh_config': ssh_config,
            'html_input_values': html_input_values,
        }

        socketio.start_background_task(
            run_installation, socketio, installation.id, session_factory, config_file, install_params,
        )

        return redirect(url_for('show_install_progress', installation_id=installation.id))

    elif verify_login(database) == 'desactivated':
        return redirect(url_for('sso_login', error='2'))
    else:
        return redirect(url_for('sso_login'))
