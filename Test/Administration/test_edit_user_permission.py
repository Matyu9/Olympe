import requests

from Utils.Database.permission import Permission

EDIT_PERMISSION_URL = "/admin/user/edit_permission/"


def test_redirects_when_not_logged_in(base_url):
    response = requests.post(
        f"{base_url}{EDIT_PERMISSION_URL}",
        json={"token": "whatever", "permission_name": "show_log", "value": True},
        allow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/sso/login/?error=0"  # via le hook global verify_maintenance


def test_redirects_when_missing_edit_permission(base_url, make_user, login_as):
    actor = make_user()  # aucune permission
    target = make_user()

    session = login_as(actor["username"], actor["password"])
    response = session.post(
        f"{base_url}{EDIT_PERMISSION_URL}",
        json={"token": target["token"], "permission_name": "show_log", "value": True},
        allow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/admin/user/"


def test_edit_permission_holder_can_edit_a_regular_permission(base_url, make_user, login_as, db_session):
    actor = make_user(edit_permission=True)
    target = make_user()

    session = login_as(actor["username"], actor["password"])
    response = session.post(
        f"{base_url}{EDIT_PERMISSION_URL}",
        json={"token": target["token"], "permission_name": "show_log", "value": True},
    )

    assert response.status_code == 200
    assert response.json()["permission"] == "show_log"

    db_session.expire_all()
    updated = db_session.query(Permission).filter(Permission.user_token == target["token"]).first()
    assert updated.show_log is True


def test_unknown_permission_name_is_rejected(base_url, make_user, login_as):
    """Régression sécurité : `permission_name` doit être whitelisté aux colonnes réelles de
    `Permission`, sinon un nom de colonne arbitraire (interne, non-booléenne...) pourrait être
    ciblé par l'update SQLAlchemy."""
    actor = make_user(admin=True)
    target = make_user()

    session = login_as(actor["username"], actor["password"])
    response = session.post(
        f"{base_url}{EDIT_PERMISSION_URL}",
        json={"token": target["token"], "permission_name": "user_token", "value": "hijacked"},
    )

    assert response.status_code == 400


def test_edit_permission_holder_cannot_self_grant_admin(base_url, make_user, login_as, db_session):
    """Régression sécurité (élévation de privilèges) : détenir `edit_permission` seul ne doit
    plus permettre de toucher à la colonne `admin`, sans quoi un utilisateur peut se
    l'auto-attribuer via `edit_user_permission_cogs`."""
    actor = make_user(edit_permission=True)

    session = login_as(actor["username"], actor["password"])
    response = session.post(
        f"{base_url}{EDIT_PERMISSION_URL}",
        json={"token": actor["token"], "permission_name": "admin", "value": True},
    )

    assert response.status_code == 403

    db_session.expire_all()
    updated = db_session.query(Permission).filter(Permission.user_token == actor["token"]).first()
    assert updated.admin is False


def test_admin_can_grant_admin(base_url, make_user, login_as, db_session):
    actor = make_user(admin=True)
    target = make_user()

    session = login_as(actor["username"], actor["password"])
    response = session.post(
        f"{base_url}{EDIT_PERMISSION_URL}",
        json={"token": target["token"], "permission_name": "admin", "value": True},
    )

    assert response.status_code == 200

    db_session.expire_all()
    updated = db_session.query(Permission).filter(Permission.user_token == target["token"]).first()
    assert updated.admin is True
