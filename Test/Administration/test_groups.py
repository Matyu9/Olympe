from Utils.Database.group import Group
from Utils.Database.group_member import GroupMember
from Utils.Database.module_access import ModuleAccess

GROUPS_URL = "/admin/groups/"
DELETE_GROUP_URL = "/admin/groups/delete/"


def test_edit_group_updates_name_and_description(base_url, make_user, login_as, make_group, db_session):
    actor = make_user(on_off_modules=True)
    group = make_group()

    session = login_as(actor["username"], actor["password"])
    response = session.post(
        base_url + GROUPS_URL,
        data={"group_id": group.id, "group_name": "Nouveau nom", "group_description": "Nouvelle description"},
        allow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"] == f"/admin/groups/?group_id={group.id}"

    db_session.rollback()  # repart sur un instantane frais (REPEATABLE READ), cf. Test/Administration/Modules/test_install_module.py
    updated = db_session.query(Group).filter(Group.id == group.id).first()
    assert updated.name == "Nouveau nom"
    assert updated.description == "Nouvelle description"


def test_delete_group_removes_group_and_cascades_members_and_module_access(
    base_url, make_user, login_as, make_group, make_module, db_session
):
    actor = make_user(on_off_modules=True)
    member = make_user()
    module = make_module(restricted_access=True)
    group = make_group()

    db_session.add(GroupMember(group_id=group.id, user_token=member["token"]))
    db_session.add(ModuleAccess(module_id=module.id, group_id=group.id))
    db_session.commit()
    group_id = group.id

    session = login_as(actor["username"], actor["password"])
    response = session.post(base_url + DELETE_GROUP_URL, data={"group_id_to_delete": group_id}, allow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/admin/groups/"

    db_session.rollback()  # repart sur un instantane frais (REPEATABLE READ), cf. Test/Administration/Modules/test_install_module.py
    assert db_session.query(Group).filter(Group.id == group_id).first() is None
    assert db_session.query(GroupMember).filter(GroupMember.group_id == group_id).first() is None
    assert db_session.query(ModuleAccess).filter(ModuleAccess.group_id == group_id).first() is None
