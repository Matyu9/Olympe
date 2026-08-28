import os
import shutil
import subprocess
import sys
from pathlib import Path


def _find_bash() -> str:
    """Localise un interpréteur bash pour exécuter install-script. `bash` est rarement sur le
    PATH d'un process Windows même quand Git for Windows est installé (seuls git.exe et les shims
    cmd le sont) : on retombe sur ses emplacements d'installation standards avant d'abandonner."""
    found = shutil.which('bash')
    if found:
        return found

    if sys.platform == 'win32':
        candidates = []
        for env_var in ('ProgramFiles', 'ProgramFiles(x86)', 'ProgramW6432'):
            base = os.environ.get(env_var)
            if base:
                candidates.append(Path(base) / 'Git' / 'bin' / 'bash.exe')
                candidates.append(Path(base) / 'Git' / 'usr' / 'bin' / 'bash.exe')
        for candidate in candidates:
            if candidate.is_file():
                return str(candidate)

    raise RuntimeError(
        "Impossible de trouver 'bash' pour exécuter install-script. Installe Git for Windows "
        "(https://git-scm.com/download/win) ou WSL, ou ajoute 'bash' au PATH."
    )


def clone(url_repo: str, path_to_clone: str):
    subprocess.run(['git', 'clone', url_repo, path_to_clone], check=True)


def run_install_script(path_to_clone: str, install_script: str, on_line):
    """Lance le script d'installation du module et transmet chaque ligne de sortie à `on_line`
    au fur et à mesure qu'elle est produite (pas d'attente de la fin du script)."""
    script_path = f'{path_to_clone.rstrip("/")}/{install_script}'
    process = subprocess.Popen(
        [_find_bash(), script_path],
        cwd=path_to_clone,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    for line in process.stdout:
        on_line(line.rstrip('\n'))

    exit_code = process.wait()
    if exit_code != 0:
        raise RuntimeError(f"install-script exited with code {exit_code}")
