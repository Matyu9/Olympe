import subprocess


def clone(url_repo: str, path_to_clone: str):
    subprocess.run(['git', 'clone', url_repo, path_to_clone], check=True)


def run_install_script(path_to_clone: str, install_script: str, on_line):
    """Lance le script d'installation du module et transmet chaque ligne de sortie à `on_line`
    au fur et à mesure qu'elle est produite (pas d'attente de la fin du script)."""
    script_path = f'{path_to_clone.rstrip("/")}/{install_script}'
    process = subprocess.Popen(
        ['bash', script_path],
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
