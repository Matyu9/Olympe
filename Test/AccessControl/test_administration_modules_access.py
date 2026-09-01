import pytest

from Utils.Database.modules import Module
from Utils.Database.module_installation import ModuleInstallation

# Repetitif par nature (une garde presque identique verifiee route par route) : exclu du
# `pytest` classique, voir pytest.ini. Lancer avec `pytest -m access_control`.
pytestmark = pytest.mark.access_control


def test_show_modules_redirects_when_missing_permission(base_url, make_user, login_as):
    user = make_user()  # add_modules=False par defaut
    session = login_as(user["username"], user["password"])

    response = session.get(f"{base_url}/admin/modules/", allow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_show_modules_accessible_with_add_modules_permission(base_url, make_user, login_as):
    user = make_user(add_modules=True)
    session = login_as(user["username"], user["password"])

    response = session.get(f"{base_url}/admin/modules/")

    assert response.status_code == 200


def test_show_modules_hides_restricted_module_without_show_all_modules(base_url, make_user, login_as, make_module):
    """Regression : `add_modules` ("Ajouter un module") ne doit pas donner la visibilite sur les
    modules a acces restreint - seul `show_all_modules`/`admin`/un acces explicite le permet
    (cf. Utils/Administration/Modules/module_access.py)."""
    user = make_user(add_modules=True)
    open_module = make_module(restricted_access=False)
    restricted_module = make_module(restricted_access=True)
    session = login_as(user["username"], user["password"])

    response = session.get(f"{base_url}/admin/modules/")

    assert response.status_code == 200
    assert open_module.name in response.text
    assert restricted_module.name not in response.text


def test_show_modules_detail_redirects_for_restricted_module_without_access(base_url, make_user, login_as, make_module):
    user = make_user(add_modules=True)
    restricted_module = make_module(restricted_access=True)
    session = login_as(user["username"], user["password"])

    response = session.get(
        f"{base_url}/admin/modules/?module_token={restricted_module.token}", allow_redirects=False
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/admin/modules/"


def test_show_modules_detail_accessible_for_restricted_module_with_show_all_modules(base_url, make_user, login_as, make_module):
    user = make_user(add_modules=True, show_all_modules=True)
    restricted_module = make_module(restricted_access=True)
    session = login_as(user["username"], user["password"])

    response = session.get(f"{base_url}/admin/modules/?module_token={restricted_module.token}")

    assert response.status_code == 200


def test_edit_module_denies_restricted_module_without_access(base_url, make_user, login_as, make_module, db_session):
    user = make_user(add_modules=True)
    restricted_module = make_module(restricted_access=True)
    original_name = restricted_module.name
    session = login_as(user["username"], user["password"])

    response = session.post(
        f"{base_url}/admin/modules/",
        data={
            "token": restricted_module.token,
            "module_name": "nom-usurpe",
            "module_url": restricted_module.fqdn,
            "socket_url": "/socket/",
        },
        allow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/admin/modules/"

    db_session.rollback()  # repart sur un instantane frais (REPEATABLE READ), cf. Test/Administration/Modules/test_install_module.py
    assert db_session.query(Module).filter(Module.token == restricted_module.token).first().name == original_name


def test_add_modules_form_redirects_when_missing_permission(base_url, make_user, login_as):
    user = make_user()
    session = login_as(user["username"], user["password"])

    response = session.get(f"{base_url}/admin/modules/add/", allow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_add_modules_form_accessible_with_permission(base_url, make_user, login_as):
    user = make_user(add_modules=True)
    session = login_as(user["username"], user["password"])

    response = session.get(f"{base_url}/admin/modules/add/")

    assert response.status_code == 200


def test_show_install_form_redirects_when_missing_permission(base_url, make_user, login_as):
    user = make_user()
    session = login_as(user["username"], user["password"])

    response = session.get(f"{base_url}/admin/modules/install/", allow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_maintenance_redirects_when_missing_permission(base_url, make_user, login_as, make_module):
    user = make_user()  # on_off_maintenance=False par defaut
    module = make_module()
    session = login_as(user["username"], user["password"])

    response = session.post(
        f"{base_url}/admin/modules/maintenance/",
        data={"module_name": "un-autre-module", "module_token": module.token},
        allow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_maintenance_toggle_with_permission(base_url, make_user, login_as, make_module, db_session):
    user = make_user(on_off_maintenance=True)
    module = make_module()
    assert module.maintenance is False
    session = login_as(user["username"], user["password"])

    response = session.post(
        f"{base_url}/admin/modules/maintenance/",
        data={"module_name": "un-autre-module", "module_token": module.token},
        allow_redirects=False,
    )

    assert response.status_code == 302

    db_session.rollback()  # repart sur un instantane frais (REPEATABLE READ), cf. Test/Administration/Modules/test_install_module.py
    assert db_session.query(Module).filter(Module.token == module.token).first().maintenance is True


def test_regenerate_secret_redirects_when_add_modules_but_not_admin(base_url, make_user, login_as, make_module):
    """Regression : regenerate_secret exige `admin` specifiquement, add_modules seul ne suffit
    pas (contrairement a la plupart des autres routes de ce dossier)."""
    user = make_user(add_modules=True)
    module = make_module()
    session = login_as(user["username"], user["password"])

    response = session.post(
        f"{base_url}/admin/modules/regenerate_secret/", data={"module_token": module.token}, allow_redirects=False
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_regenerate_secret_with_admin(base_url, make_user, login_as, make_module, db_session):
    user = make_user(admin=True)
    module = make_module()
    original_secret = module.client_secret
    session = login_as(user["username"], user["password"])

    response = session.post(
        f"{base_url}/admin/modules/regenerate_secret/", data={"module_token": module.token}
    )

    assert response.status_code == 200

    db_session.rollback()  # repart sur un instantane frais (REPEATABLE READ), cf. Test/Administration/Modules/test_install_module.py
    assert db_session.query(Module).filter(Module.token == module.token).first().client_secret != original_secret


def test_show_install_progress_redirects_when_missing_permission(base_url, make_user, login_as, db_session):
    user = make_user()
    installation = ModuleInstallation(name="_pytest_install", status="pending", created_at=0, updated_at=0)
    db_session.add(installation)
    db_session.commit()
    session = login_as(user["username"], user["password"])

    try:
        response = session.get(f"{base_url}/admin/modules/install/{installation.id}/", allow_redirects=False)

        assert response.status_code == 302
        assert response.headers["Location"] == "/"
    finally:
        db_session.delete(installation)
        db_session.commit()


def test_show_install_progress_accessible_with_permission(base_url, make_user, login_as, db_session):
    user = make_user(add_modules=True)
    installation = ModuleInstallation(name="_pytest_install", status="pending", created_at=0, updated_at=0)
    db_session.add(installation)
    db_session.commit()
    session = login_as(user["username"], user["password"])

    try:
        response = session.get(f"{base_url}/admin/modules/install/{installation.id}/")

        assert response.status_code == 200
    finally:
        db_session.delete(installation)
        db_session.commit()


def test_show_install_progress_unknown_id_redirects_to_show_modules(base_url, make_user, login_as):
    user = make_user(add_modules=True)
    session = login_as(user["username"], user["password"])

    response = session.get(f"{base_url}/admin/modules/install/999999999/", allow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/admin/modules/"
