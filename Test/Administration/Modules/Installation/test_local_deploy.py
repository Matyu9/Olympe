import subprocess

import pytest

from Utils.Administration.Modules.Installation import local_deploy


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


def test_run_install_script_streams_lines_in_order(tmp_path):
    repo = _make_git_repo(tmp_path / "repo", "#!/bin/bash\necho line-one\necho line-two\nexit 0\n")
    target = tmp_path / "cloned"
    local_deploy.clone(str(repo), str(target))

    lines = []
    local_deploy.run_install_script(str(target), "install.sh", lines.append)

    assert lines == ["line-one", "line-two"]


def test_run_install_script_raises_on_non_zero_exit(tmp_path):
    repo = _make_git_repo(tmp_path / "repo", "#!/bin/bash\necho before-fail\nexit 3\n")
    target = tmp_path / "cloned"
    local_deploy.clone(str(repo), str(target))

    lines = []
    with pytest.raises(RuntimeError):
        local_deploy.run_install_script(str(target), "install.sh", lines.append)

    assert lines == ["before-fail"]
