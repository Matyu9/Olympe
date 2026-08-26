from time import time
from uuid import uuid3, uuid1
from secrets import token_urlsafe
from argon2 import PasswordHasher

from Utils.Database.modules import Module
from Utils.Database.module_installation import ModuleInstallation
from Utils.Administration.Modules.Installation import local_deploy, ssh_deploy, config_injection


def _set_status(database, socketio, room, installation, status, message=None):
    installation.status = status
    installation.status_message = message
    installation.updated_at = round(time())
    database.commit()
    socketio.emit('module_install_progress', {'status': status, 'message': message}, room=room)


def run_installation(socketio, installation_id, session_factory, config_file, install_params):
    """Orchestrateur de l'installation, lancé via socketio.start_background_task. `install_params`
    regroupe tout ce que l'admin a saisi dans le formulaire de déploiement (jamais lu depuis
    config_file, qui est le manifeste du module)."""
    database = session_factory()
    room = str(installation_id)

    try:
        installation = database.query(ModuleInstallation).filter(ModuleInstallation.id == installation_id).first()

        install_target = install_params['install_target']
        path_to_clone = install_params['path_to_clone']
        module_fqdn = install_params['module_fqdn']
        olympe_url = install_params['olympe_url']
        ssh_config = install_params.get('ssh_config')
        settings = install_params.get('html_input_values', {})

        def on_line(line):
            socketio.emit('module_install_progress', {'status': 'installing', 'message': line}, room=room)

        _set_status(database, socketio, room, installation, 'cloning')
        if install_target == 'local':
            local_deploy.clone(config_file['url-repo'], path_to_clone)
        else:
            ssh_deploy.clone(ssh_config, config_file['url-repo'], path_to_clone)

        _set_status(database, socketio, room, installation, 'registering')
        token = str(uuid3(uuid1(), str(uuid1())))
        plain_secret = token_urlsafe(32)
        module = Module(
            token=token,
            name=config_file['name'],
            fqdn=module_fqdn,
            maintenance=False,
            require_consent=False,
            client_secret=PasswordHasher().hash(plain_secret),
        )
        database.add(module)
        installation.module_token = token
        database.commit()

        _set_status(database, socketio, room, installation, 'configuring')
        config_injection.write_config(
            install_target, ssh_config, path_to_clone,
            config_file['name'], token, plain_secret, module_fqdn, olympe_url, settings,
        )

        _set_status(database, socketio, room, installation, 'installing')
        install_script = config_file['configuration']['install-script']
        if install_target == 'local':
            local_deploy.run_install_script(path_to_clone, install_script, on_line)
        else:
            ssh_deploy.run_install_script(ssh_config, path_to_clone, install_script, on_line)

        _set_status(database, socketio, room, installation, 'done')
        socketio.emit('module_install_done', {'module_token': token, 'plain_secret': plain_secret}, room=room)

    except Exception as e:
        _set_status(database, socketio, room, installation, 'failed', str(e))
        socketio.emit('module_install_error', {'message': str(e)}, room=room)
    finally:
        database.close()
