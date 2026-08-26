import json
import re
import unicodedata

from Utils.Administration.Modules.Installation.ssh_deploy import _connect as ssh_connect


def _slugify(name: str) -> str:
    normalized = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode()
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', normalized).strip('-').lower()
    return slug or 'module'


def write_config(install_target: str, ssh_config: dict, path_to_clone: str, module_name: str,
                  client_id: str, client_secret: str, module_fqdn: str, socket_url: str, settings: dict) -> str:
    """Écrit le fichier de config du module (nommé d'après lui, pas un nom générique côté Olympe)
    à la racine de path_to_clone, en local ou via SFTP selon install_target. Renvoie le nom du
    fichier écrit."""
    content = {
        'module_name': module_name,
        'client_id': client_id,
        'client_secret': client_secret,
        'module_fqdn': module_fqdn,
        'socket_url': socket_url,
        'settings': settings,
    }
    filename = f'{_slugify(module_name)}-config.json'
    file_path = f'{path_to_clone.rstrip("/")}/{filename}'
    raw = json.dumps(content, indent=2)

    if install_target == 'local':
        with open(file_path, 'w') as f:
            f.write(raw)
    else:
        client = ssh_connect(ssh_config)
        try:
            sftp = client.open_sftp()
            try:
                with sftp.open(file_path, 'w') as f:
                    f.write(raw)
            finally:
                sftp.close()
        finally:
            client.close()

    return filename
