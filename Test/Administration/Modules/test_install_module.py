import json
import re
import subprocess
import time

import requests

from Utils.Database.module_installation import ModuleInstallation
from Utils.Database.modules import Module

VALID_MANIFEST = {
    "name": "_pytest_ecosystem_module",
    "url-repo": "unused-for-manifest-validation-tests",
    "guidelines": "#",
    "beta": False,
    "configuration": {
        "html-input": {
            "greeting": {"type": "text", "default-value": "hello"},
        },
        "install-script": "install.sh",
    },
}


def _make_git_repo_with_install_script(path, script_body):
    path.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.invalid"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=path, check=True)
    (path / "install.sh").write_text(script_body)
    subprocess.run(["git", "add", "install.sh"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=path, check=True)
    return path


def _wait_for_final_status(db_session, installation_id, timeout=15):
    """L'installation tourne dans un thread de fond côté serveur, sur sa propre connexion DB.
    Sous MySQL (REPEATABLE READ), notre session de lecture reste sur l'instantané pris à sa
    première requête tant qu'on ne commit/rollback pas — il faut donc explicitement démarrer une
    nouvelle transaction à chaque itération pour voir les changements du thread de fond."""
    deadline = time.time() + timeout
    installation = None
    while time.time() < deadline:
        db_session.rollback()
        installation = db_session.query(ModuleInstallation).filter(ModuleInstallation.id == installation_id).first()
        if installation is not None and installation.status in ("done", "failed"):
            return installation
        time.sleep(0.2)
    raise AssertionError(f"installation {installation_id} still '{installation and installation.status}' after {timeout}s")


def test_install_form_redirects_when_not_logged_in(base_url):
    response = requests.get(f"{base_url}/admin/modules/install/", allow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/sso/login/?error=0"


def test_install_form_redirects_when_logged_in_without_permission(base_url, make_user, login_as):
    user = make_user()  # add_modules=False par défaut

    session = login_as(user["username"], user["password"])
    response = session.get(f"{base_url}/admin/modules/install/", allow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_install_form_accessible_with_add_modules_permission(base_url, make_user, login_as):
    user = make_user(add_modules=True)

    session = login_as(user["username"], user["password"])
    response = session.get(f"{base_url}/admin/modules/install/")

    assert response.status_code == 200


def test_start_install_rejects_invalid_manifest(base_url, make_user, login_as):
    user = make_user(add_modules=True)
    session = login_as(user["username"], user["password"])

    response = session.post(f"{base_url}/admin/modules/install/start/", data={
        "manifest_json": json.dumps({"name": "incomplet"}),
        "install_target": "local",
        "path_to_clone": "unused",
        "module_fqdn": "https://module.example.invalid",
    })

    assert response.status_code == 200
    assert "parameter missing" in response.text


def test_start_install_rejects_when_missing_permission(base_url, make_user, login_as):
    user = make_user()

    session = login_as(user["username"], user["password"])
    response = session.post(f"{base_url}/admin/modules/install/start/", data={
        "manifest_json": json.dumps(VALID_MANIFEST),
        "install_target": "local",
        "path_to_clone": "unused",
        "module_fqdn": "https://module.example.invalid",
    }, allow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_full_local_install_flow_creates_module_and_config_file(base_url, make_user, login_as, db_session, tmp_path):
    repo = _make_git_repo_with_install_script(
        tmp_path / "repo",
        "#!/bin/bash\necho installing\nexit 0\n",
    )
    target = tmp_path / "cloned"

    manifest = dict(VALID_MANIFEST, **{"url-repo": str(repo)})

    user = make_user(add_modules=True)
    session = login_as(user["username"], user["password"])

    response = session.post(f"{base_url}/admin/modules/install/start/", data={
        "manifest_json": json.dumps(manifest),
        "install_target": "local",
        "path_to_clone": str(target),
        "module_fqdn": "https://module.example.invalid",
        "html_input__greeting": "hi",
    }, allow_redirects=False)

    assert response.status_code == 302
    match = re.match(r"^/admin/modules/install/(\d+)/$", response.headers["Location"])
    assert match, f"unexpected redirect location: {response.headers['Location']}"
    installation_id = int(match.group(1))

    installation = None
    module = None
    try:
        installation = _wait_for_final_status(db_session, installation_id)

        assert installation.status == "done", installation.status_message
        assert installation.module_token is not None

        module = db_session.query(Module).filter(Module.token == installation.module_token).first()
        assert module is not None
        assert module.name == manifest["name"]
        assert module.fqdn == "https://module.example.invalid"

        config_file = target / "pytest-ecosystem-module-config.json"
        assert config_file.exists()
        content = json.loads(config_file.read_text())
        assert content["module_name"] == manifest["name"]
        assert content["client_id"] == installation.module_token
        assert content["settings"] == {"greeting": "hi"}
    finally:
        if module is not None:
            db_session.delete(module)
        if installation is not None:
            db_session.delete(installation)
        db_session.commit()
