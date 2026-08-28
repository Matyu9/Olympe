import subprocess

import pytest

from Utils.Administration.Modules.Installation import local_deploy


def _bash_available():
    try:
        local_deploy._find_bash()
        return True
    except RuntimeError:
        return False


# run_install_script() a besoin d'un interpréteur bash (local_deploy._find_bash) : sur une machine
# sans Git for Windows ni WSL installé, aucun n'est trouvable — dernier recours, on saute plutôt
# que de faire échouer le test pour une raison hors de portée du code testé.
requires_bash = pytest.mark.skipif(
    not _bash_available(),
    reason="aucun interpréteur bash trouvable (installe Git for Windows ou WSL)",
)


def _make_git_repo(path, script_body):
    path.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.invalid"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=path, check=True)

    script_path = path / "install.sh"
    script_path.write_text(script_body)

    subprocess.run(["git", "add", "install.sh"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=path, check=True)
    return path


def test_clone_copies_repo_content(tmp_path):
    repo = _make_git_repo(tmp_path / "repo", "#!/bin/bash\nexit 0\n")
    target = tmp_path / "cloned"

    local_deploy.clone(str(repo), str(target))

    assert (target / "install.sh").exists()


@requires_bash
def test_run_install_script_streams_lines_in_order(tmp_path):
    repo = _make_git_repo(tmp_path / "repo", "#!/bin/bash\necho line-one\necho line-two\nexit 0\n")
    target = tmp_path / "cloned"
    local_deploy.clone(str(repo), str(target))

    lines = []
    local_deploy.run_install_script(str(target), "install.sh", lines.append)

    assert lines == ["line-one", "line-two"]


@requires_bash
def test_run_install_script_raises_on_non_zero_exit(tmp_path):
    repo = _make_git_repo(tmp_path / "repo", "#!/bin/bash\necho before-fail\nexit 3\n")
    target = tmp_path / "cloned"
    local_deploy.clone(str(repo), str(target))

    lines = []
    with pytest.raises(RuntimeError):
        local_deploy.run_install_script(str(target), "install.sh", lines.append)

    assert lines == ["before-fail"]


def test_find_bash_prefers_the_one_already_on_path(monkeypatch):
    monkeypatch.setattr(local_deploy.shutil, "which", lambda name: r"C:\fake\on-path\bash.exe" if name == "bash" else None)

    assert local_deploy._find_bash() == r"C:\fake\on-path\bash.exe"


def test_find_bash_falls_back_to_git_for_windows_install_location(monkeypatch, tmp_path):
    """Régression : sous Windows, Git for Windows met git.exe sur le PATH mais pas bash.exe —
    _find_bash() doit quand même le retrouver dans l'arborescence d'installation standard."""
    fake_git_bash = tmp_path / "Git" / "bin" / "bash.exe"
    fake_git_bash.parent.mkdir(parents=True)
    fake_git_bash.write_text("")

    monkeypatch.setattr(local_deploy.shutil, "which", lambda name: None)
    monkeypatch.setattr(local_deploy.sys, "platform", "win32")
    monkeypatch.setenv("ProgramFiles", str(tmp_path))
    monkeypatch.delenv("ProgramFiles(x86)", raising=False)
    monkeypatch.delenv("ProgramW6432", raising=False)

    assert local_deploy._find_bash() == str(fake_git_bash)


def test_find_bash_raises_a_clear_error_when_nothing_is_found(monkeypatch):
    monkeypatch.setattr(local_deploy.shutil, "which", lambda name: None)
    monkeypatch.setattr(local_deploy.sys, "platform", "win32")
    monkeypatch.delenv("ProgramFiles", raising=False)
    monkeypatch.delenv("ProgramFiles(x86)", raising=False)
    monkeypatch.delenv("ProgramW6432", raising=False)

    with pytest.raises(RuntimeError, match="bash"):
        local_deploy._find_bash()
