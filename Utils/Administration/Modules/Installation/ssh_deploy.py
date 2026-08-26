import shlex
import paramiko


def _connect(ssh_config: dict) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=ssh_config['ssh-url'],
        port=int(ssh_config['ssh-port']),
        username=ssh_config['ssh-username'],
        password=ssh_config['ssh-password'],
    )
    return client


def _run_and_stream(client: paramiko.SSHClient, command: str, on_line=None):
    stdin, stdout, channel_stderr = client.exec_command(command)
    channel = stdout.channel
    for line in stdout:
        if on_line:
            on_line(line.rstrip('\n'))
    exit_code = channel.recv_exit_status()
    if exit_code != 0:
        raise RuntimeError(f"remote command exited with code {exit_code}: {command}")


def clone(ssh_config: dict, url_repo: str, path_to_clone: str):
    client = _connect(ssh_config)
    try:
        command = f'git clone {shlex.quote(url_repo)} {shlex.quote(path_to_clone)}'
        _run_and_stream(client, command)
    finally:
        client.close()


def run_install_script(ssh_config: dict, path_to_clone: str, install_script: str, on_line):
    """Lance le script d'installation du module côté distant et transmet chaque ligne de sortie
    à `on_line` au fur et à mesure qu'elle est produite (paramiko ne bloque pas jusqu'à la fin de
    la commande, on peut itérer sur le flux stdout pendant l'exécution)."""
    client = _connect(ssh_config)
    try:
        script_path = f'{path_to_clone.rstrip("/")}/{install_script}'
        command = f'bash {shlex.quote(script_path)}'
        _run_and_stream(client, command, on_line)
    finally:
        client.close()
