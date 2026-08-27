from Utils.Administration.Modules.module_access import user_can_access_module
from Utils.Database.module_access import ModuleAccess
from Utils.Database.group_member import GroupMember
from Utils.Database.user import User


def _get_user(db_session, token):
    return db_session.query(User).filter(User.token == token).first()


def test_unrestricted_module_is_always_accessible(db_session, make_user, make_module):
    user = _get_user(db_session, make_user()["token"])
    module = make_module(restricted_access=False)

    assert user_can_access_module(db_session, user, module) is True


def test_restricted_module_denies_user_without_access(db_session, make_user, make_module):
    user = _get_user(db_session, make_user()["token"])
    module = make_module(restricted_access=True)

    assert user_can_access_module(db_session, user, module) is False


def test_restricted_module_allows_direct_user_access(db_session, make_user, make_module):
    user = _get_user(db_session, make_user()["token"])
    module = make_module(restricted_access=True)

    db_session.add(ModuleAccess(module_id=module.id, user_token=user.token))
    db_session.commit()

    assert user_can_access_module(db_session, user, module) is True


def test_restricted_module_allows_access_via_group_membership(db_session, make_user, make_module, make_group):
    user = _get_user(db_session, make_user()["token"])
    module = make_module(restricted_access=True)
    group = make_group()

    db_session.add(GroupMember(group_id=group.id, user_token=user.token))
    db_session.add(ModuleAccess(module_id=module.id, group_id=group.id))
    db_session.commit()

    assert user_can_access_module(db_session, user, module) is True


def test_restricted_module_still_denies_unrelated_group_member(db_session, make_user, make_module, make_group):
    user = _get_user(db_session, make_user()["token"])
    module = make_module(restricted_access=True)
    group = make_group()  # l'utilisateur n'est pas ajouté à ce groupe

    db_session.add(ModuleAccess(module_id=module.id, group_id=group.id))
    db_session.commit()

    assert user_can_access_module(db_session, user, module) is False


def test_olympe_admin_bypasses_module_restriction(db_session, make_user, make_module):
    user = _get_user(db_session, make_user(admin=True)["token"])
    module = make_module(restricted_access=True)

    assert user_can_access_module(db_session, user, module) is True
