from Utils.Database.group_member import GroupMember
from Utils.Database.group_permission_override import GroupPermissionOverride
from Utils.permission_resolution import (
    get_effective_permission, get_group_permission_sources, get_other_group_overrides_for_group,
)

EDIT_GROUP_PERMISSION_URL = "/admin/groups/permission/"


# --- Resolution (Utils/permission_resolution.py) ---------------------------------------------

def test_effective_permission_falls_back_to_personal_value_without_override(make_user, db_session):
    user = make_user(on_off_modules=True)

    assert get_effective_permission(db_session, user["token"], "on_off_modules") is True
    assert get_effective_permission(db_session, user["token"], "edit_permission") is False


def test_effective_permission_is_forced_by_single_group_override(make_user, make_group, db_session):
    user = make_user(edit_permission=True)
    group = make_group()
    db_session.add(GroupMember(group_id=group.id, user_token=user["token"]))
    db_session.add(GroupPermissionOverride(group_id=group.id, permission_name="edit_permission", value=False))
    db_session.commit()

    assert get_effective_permission(db_session, user["token"], "edit_permission") is False


def test_effective_permission_uses_highest_priority_group_on_conflict(make_user, make_group, db_session):
    user = make_user()
    low_priority_group = make_group(priority=1)
    high_priority_group = make_group(priority=5)
    db_session.add(GroupMember(group_id=low_priority_group.id, user_token=user["token"]))
    db_session.add(GroupMember(group_id=high_priority_group.id, user_token=user["token"]))
    db_session.add(GroupPermissionOverride(group_id=low_priority_group.id, permission_name="on_off_modules", value=False))
    db_session.add(GroupPermissionOverride(group_id=high_priority_group.id, permission_name="on_off_modules", value=True))
    db_session.commit()

    assert get_effective_permission(db_session, user["token"], "on_off_modules") is True


def test_effective_permission_false_wins_on_equal_priority_conflict(make_user, make_group, db_session):
    user = make_user()
    group_a = make_group(priority=3)
    group_b = make_group(priority=3)
    db_session.add(GroupMember(group_id=group_a.id, user_token=user["token"]))
    db_session.add(GroupMember(group_id=group_b.id, user_token=user["token"]))
    db_session.add(GroupPermissionOverride(group_id=group_a.id, permission_name="on_off_modules", value=True))
    db_session.add(GroupPermissionOverride(group_id=group_b.id, permission_name="on_off_modules", value=False))
    db_session.commit()

    assert get_effective_permission(db_session, user["token"], "on_off_modules") is False


def test_effective_permission_applies_both_overrides_when_groups_touch_different_permissions(
    make_user, make_group, db_session
):
    """La priorité ne départage que les groupes qui forcent la MÊME permission : deux groupes qui
    touchent des permissions différentes s'appliquent tous les deux, indépendamment de leur priorité."""
    user = make_user()
    low_priority_group = make_group(priority=1)
    high_priority_group = make_group(priority=10)
    db_session.add(GroupMember(group_id=low_priority_group.id, user_token=user["token"]))
    db_session.add(GroupMember(group_id=high_priority_group.id, user_token=user["token"]))
    db_session.add(GroupPermissionOverride(group_id=low_priority_group.id, permission_name="create_user", value=True))
    db_session.add(GroupPermissionOverride(group_id=high_priority_group.id, permission_name="edit_permission", value=True))
    db_session.commit()

    assert get_effective_permission(db_session, user["token"], "create_user") is True
    assert get_effective_permission(db_session, user["token"], "edit_permission") is True

    sources = get_group_permission_sources(db_session, user["token"])
    assert sources["create_user"] == {
        "value": True, "groups": [low_priority_group.name], "conflict": False, "dissenting_groups": [],
    }
    assert sources["edit_permission"] == {
        "value": True, "groups": [high_priority_group.name], "conflict": False, "dissenting_groups": [],
    }


def test_effective_permission_flags_conflict_when_groups_disagree(make_user, make_group, db_session):
    """Quand des groupes se contredisent sur la même permission (même si l'un d'eux ne l'emporte
    pas faute de priorité), `get_group_permission_sources` doit le signaler pour l'affichage
    (page utilisateur) — cf. `conflict`/`dissenting_groups`."""
    user = make_user()
    low_priority_group = make_group(priority=1)
    high_priority_group = make_group(priority=10)
    db_session.add(GroupMember(group_id=low_priority_group.id, user_token=user["token"]))
    db_session.add(GroupMember(group_id=high_priority_group.id, user_token=user["token"]))
    db_session.add(GroupPermissionOverride(group_id=low_priority_group.id, permission_name="on_off_modules", value=False))
    db_session.add(GroupPermissionOverride(group_id=high_priority_group.id, permission_name="on_off_modules", value=True))
    db_session.commit()

    sources = get_group_permission_sources(db_session, user["token"])
    assert sources["on_off_modules"] == {
        "value": True, "groups": [high_priority_group.name],
        "conflict": True, "dissenting_groups": [low_priority_group.name],
    }


def test_other_group_overrides_reports_groups_touching_the_same_permission(make_group, db_session):
    group_a = make_group(priority=1)
    group_b = make_group(priority=5)
    group_c = make_group()  # ne touche à rien : ne doit apparaître nulle part
    db_session.add(GroupPermissionOverride(group_id=group_a.id, permission_name="create_user", value=True))
    db_session.add(GroupPermissionOverride(group_id=group_b.id, permission_name="create_user", value=False))
    db_session.add(GroupPermissionOverride(group_id=group_a.id, permission_name="edit_permission", value=True))
    db_session.commit()

    others_for_a = get_other_group_overrides_for_group(db_session, group_a.id)
    assert others_for_a == {"create_user": [{"group": group_b.name, "value": False, "priority": 5}]}

    others_for_b = get_other_group_overrides_for_group(db_session, group_b.id)
    assert others_for_b == {"create_user": [{"group": group_a.name, "value": True, "priority": 1}]}

    others_for_c = get_other_group_overrides_for_group(db_session, group_c.id)
    assert others_for_c == {}


def test_effective_permission_admin_bypasses_group_overrides(make_user, make_group, db_session):
    user = make_user(admin=True)
    group = make_group()
    db_session.add(GroupMember(group_id=group.id, user_token=user["token"]))
    db_session.add(GroupPermissionOverride(group_id=group.id, permission_name="on_off_modules", value=False))
    db_session.commit()

    assert get_effective_permission(db_session, user["token"], "on_off_modules") is True


# --- Endpoint (Cogs/Administration/Groups/edit_group_permission.py) --------------------------

def test_edit_group_permission_sets_override(base_url, make_user, login_as, make_group, db_session):
    actor = make_user(edit_permission=True)
    group = make_group()
    session = login_as(actor["username"], actor["password"])

    response = session.post(
        base_url + EDIT_GROUP_PERMISSION_URL,
        json={"group_id": group.id, "permission_name": "on_off_modules", "value": False},
    )

    assert response.status_code == 200
    db_session.rollback()  # repart sur un instantane frais (REPEATABLE READ), cf. Test/Administration/Modules/test_install_module.py
    override = db_session.query(GroupPermissionOverride).filter(
        GroupPermissionOverride.group_id == group.id, GroupPermissionOverride.permission_name == "on_off_modules"
    ).first()
    assert override is not None
    assert override.value is False


def test_edit_group_permission_null_value_clears_override(base_url, make_user, login_as, make_group, db_session):
    actor = make_user(edit_permission=True)
    group = make_group()
    db_session.add(GroupPermissionOverride(group_id=group.id, permission_name="on_off_modules", value=True))
    db_session.commit()
    session = login_as(actor["username"], actor["password"])

    response = session.post(
        base_url + EDIT_GROUP_PERMISSION_URL,
        json={"group_id": group.id, "permission_name": "on_off_modules", "value": None},
    )

    assert response.status_code == 200
    db_session.rollback()  # repart sur un instantane frais (REPEATABLE READ), cf. Test/Administration/Modules/test_install_module.py
    override = db_session.query(GroupPermissionOverride).filter(
        GroupPermissionOverride.group_id == group.id, GroupPermissionOverride.permission_name == "on_off_modules"
    ).first()
    assert override is None


def test_edit_group_permission_rejects_unknown_permission_name(base_url, make_user, login_as, make_group):
    actor = make_user(edit_permission=True)
    group = make_group()
    session = login_as(actor["username"], actor["password"])

    response = session.post(
        base_url + EDIT_GROUP_PERMISSION_URL,
        json={"group_id": group.id, "permission_name": "not_a_real_column", "value": True},
    )

    assert response.status_code == 400


def test_edit_group_permission_rejects_admin_column(base_url, make_user, login_as, make_group):
    """Un groupe ne doit jamais pouvoir forcer `admin` (meme risque d'escalade que pour
    edit_user_permission_cogs, cf. GROUP_OVERRIDABLE_PERMISSION_NAMES)."""
    actor = make_user(admin=True)
    group = make_group()
    session = login_as(actor["username"], actor["password"])

    response = session.post(
        base_url + EDIT_GROUP_PERMISSION_URL,
        json={"group_id": group.id, "permission_name": "admin", "value": True},
    )

    assert response.status_code == 400
