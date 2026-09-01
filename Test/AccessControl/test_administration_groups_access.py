import pytest

from Utils.Database.group_member import GroupMember

# Repetitif par nature (une garde presque identique verifiee route par route) : exclu du
# `pytest` classique, voir pytest.ini. Lancer avec `pytest -m access_control`.
pytestmark = pytest.mark.access_control


def test_show_groups_redirects_when_missing_permission(base_url, make_user, login_as):
    user = make_user()  # on_off_modules=False par defaut
    session = login_as(user["username"], user["password"])

    response = session.get(f"{base_url}/admin/groups/", allow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_show_groups_accessible_with_on_off_modules_permission(base_url, make_user, login_as):
    user = make_user(on_off_modules=True)
    session = login_as(user["username"], user["password"])

    response = session.get(f"{base_url}/admin/groups/")

    assert response.status_code == 200


def test_add_group_redirects_when_missing_permission(base_url, make_user, login_as):
    user = make_user()
    session = login_as(user["username"], user["password"])

    response = session.get(f"{base_url}/admin/groups/add/", allow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_add_group_accessible_with_on_off_modules_permission(base_url, make_user, login_as):
    user = make_user(on_off_modules=True)
    session = login_as(user["username"], user["password"])

    response = session.get(f"{base_url}/admin/groups/add/")

    assert response.status_code == 200


def test_add_group_member_redirects_when_missing_permission(base_url, make_user, login_as, make_group):
    actor = make_user()  # ni on_off_modules ni edit_permission
    target_user = make_user()
    group = make_group()
    session = login_as(actor["username"], actor["password"])

    response = session.post(
        f"{base_url}/admin/groups/members/add/",
        json={"group_id": group.id, "username": target_user["username"]},
        allow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_add_group_member_accessible_with_edit_permission_alone(base_url, make_user, login_as, make_group, db_session):
    """Regression : _can_manage_groups accepte on_off_modules OU edit_permission (pas seulement
    on_off_modules) - edit_permission seul doit donc suffire."""
    actor = make_user(edit_permission=True)
    target_user = make_user()
    group = make_group()
    session = login_as(actor["username"], actor["password"])

    response = session.post(
        f"{base_url}/admin/groups/members/add/",
        json={"group_id": group.id, "username": target_user["username"]},
    )

    assert response.status_code == 200
    assert response.json()["success"] is True

    db_session.rollback()  # repart sur un instantane frais (REPEATABLE READ), cf. Test/Administration/Modules/test_install_module.py
    member = db_session.query(GroupMember).filter(
        GroupMember.group_id == group.id, GroupMember.user_token == target_user["token"]
    ).first()
    assert member is not None


def test_remove_group_member_redirects_when_missing_permission(base_url, make_user, login_as, make_group, db_session):
    actor = make_user()
    target_user = make_user()
    group = make_group()
    member = GroupMember(group_id=group.id, user_token=target_user["token"])
    db_session.add(member)
    db_session.commit()
    session = login_as(actor["username"], actor["password"])

    response = session.post(
        f"{base_url}/admin/groups/members/remove/", json={"member_id": member.id}, allow_redirects=False
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_delete_group_redirects_when_missing_permission(base_url, make_user, login_as, make_group):
    actor = make_user()  # on_off_modules=False par defaut
    group = make_group()
    session = login_as(actor["username"], actor["password"])

    response = session.post(
        f"{base_url}/admin/groups/delete/", data={"group_id_to_delete": group.id}, allow_redirects=False
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_delete_group_accessible_with_on_off_modules_permission(base_url, make_user, login_as, make_group):
    actor = make_user(on_off_modules=True)
    group = make_group()
    session = login_as(actor["username"], actor["password"])

    response = session.post(
        f"{base_url}/admin/groups/delete/", data={"group_id_to_delete": group.id}, allow_redirects=False
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/admin/groups/"
