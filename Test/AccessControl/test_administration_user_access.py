import pytest

from Utils.Database.user import User
from Utils.Database.permission import Permission

# Repetitif par nature (une garde presque identique verifiee route par route) : exclu du
# `pytest` classique, voir pytest.ini. Lancer avec `pytest -m access_control`.
pytestmark = pytest.mark.access_control


def test_add_user_redirects_when_missing_permission(base_url, make_user, login_as):
    user = make_user()  # create_user=False par defaut
    session = login_as(user["username"], user["password"])

    response = session.get(f"{base_url}/admin/user/add/", allow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_add_user_accessible_with_create_user_permission(base_url, make_user, login_as):
    user = make_user(create_user=True)
    session = login_as(user["username"], user["password"])

    response = session.get(f"{base_url}/admin/user/add/")

    assert response.status_code == 200


def test_delete_user_redirects_when_missing_permission(base_url, make_user, login_as):
    actor = make_user()  # delete_account=False par defaut
    target = make_user()
    session = login_as(actor["username"], actor["password"])

    response = session.post(
        f"{base_url}/admin/user/delete/", data={"token_to_delete": target["token"]}, allow_redirects=False
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/admin/user/"


def test_delete_user_with_permission_actually_deletes(base_url, make_user, login_as, db_session):
    actor = make_user(delete_account=True)
    target = make_user()
    session = login_as(actor["username"], actor["password"])

    response = session.post(
        f"{base_url}/admin/user/delete/", data={"token_to_delete": target["token"]}, allow_redirects=False
    )

    assert response.status_code == 302

    db_session.rollback()  # repart sur un instantane frais (REPEATABLE READ), cf. Test/Administration/Modules/test_install_module.py
    assert db_session.query(User).filter(User.token == target["token"]).first() is None
    assert db_session.query(Permission).filter(Permission.user_token == target["token"]).first() is None


def test_desactivate_user_redirects_when_missing_permission(base_url, make_user, login_as):
    actor = make_user()  # desactivate_account=False par defaut
    target = make_user()
    session = login_as(actor["username"], actor["password"])

    response = session.post(
        f"{base_url}/admin/user/desactivate/", data={"token_to_desactivate": target["token"]}, allow_redirects=False
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/admin/user/"


def test_desactivate_user_with_permission_toggles_flag(base_url, make_user, login_as, db_session):
    actor = make_user(desactivate_account=True)
    target = make_user()
    session = login_as(actor["username"], actor["password"])

    response = session.post(
        f"{base_url}/admin/user/desactivate/", data={"token_to_desactivate": target["token"]}, allow_redirects=False
    )

    assert response.status_code == 302

    db_session.rollback()  # repart sur un instantane frais (REPEATABLE READ), cf. Test/Administration/Modules/test_install_module.py
    assert db_session.query(User).filter(User.token == target["token"]).first().desactivated is True


def test_global_permission_redirects_when_missing_any_allow_edit(base_url, make_user, login_as):
    user = make_user()  # tous les allow_edit_* a False par defaut
    session = login_as(user["username"], user["password"])

    response = session.get(f"{base_url}/admin/permission/global/", allow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/"


@pytest.mark.parametrize("allowed_flag", [
    "allow_edit_username", "allow_edit_email", "allow_edit_password",
    "allow_edit_profile_picture", "allow_edit_A2F",
])
def test_global_permission_accessible_with_any_single_allow_edit_flag(base_url, make_user, login_as, allowed_flag):
    """Regression : la regle combinee (n'importe laquelle des 5 permissions OU admin) doit
    rester satisfaite par un seul flag, pas seulement par admin."""
    user = make_user(**{allowed_flag: True})
    session = login_as(user["username"], user["password"])

    response = session.get(f"{base_url}/admin/permission/global/")

    assert response.status_code == 200


def test_global_permission_accessible_to_admin_with_no_allow_edit_flags(base_url, make_user, login_as):
    user = make_user(admin=True)
    session = login_as(user["username"], user["password"])

    response = session.get(f"{base_url}/admin/permission/global/")

    assert response.status_code == 200
