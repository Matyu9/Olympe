from flask import redirect, url_for, request, jsonify
from Utils.verify_login import verify_login

from Utils.Database.permission import Permission
from Utils.Database.user import User
from Utils.Database.group import Group
from Utils.Database.group_member import GroupMember


def _current_user_permission(database):
    return database.query(Permission).filter(Permission.user_token == request.cookies.get('token')).first()


def _can_manage_groups(user_permission):
    # Accessible depuis la page Groupes (on_off_modules) et depuis la fiche utilisateur (edit_permission)
    return user_permission.on_off_modules or user_permission.edit_permission or user_permission.admin


def add_group_member_cogs(database):
    if verify_login(database) and verify_login(database) != 'desactivated':
        user_permission = _current_user_permission(database)
        if not _can_manage_groups(user_permission):
            return redirect(url_for('home'))

        target_group = database.query(Group).filter(Group.id == request.json['group_id']).first()
        target_user = database.query(User).filter(User.username == request.json['username']).first()
        if target_group is None or target_user is None:
            return jsonify({"success": False, "error": "groupe ou utilisateur introuvable"}), 404

        existing = database.query(GroupMember).filter(
            GroupMember.group_id == target_group.id, GroupMember.user_token == target_user.token
        ).first()
        if existing is None:
            database.add(GroupMember(group_id=target_group.id, user_token=target_user.token))
            database.commit()

        return jsonify({"success": True})

    elif verify_login(database) == "desactivated":
        return redirect(url_for('sso_login', error='2'))
    else:
        return redirect(url_for('sso_login'))


def remove_group_member_cogs(database):
    if verify_login(database) and verify_login(database) != 'desactivated':
        user_permission = _current_user_permission(database)
        if not _can_manage_groups(user_permission):
            return redirect(url_for('home'))

        database.query(GroupMember).filter(GroupMember.id == request.json['member_id']).delete()
        database.commit()

        return jsonify({"success": True})

    elif verify_login(database) == "desactivated":
        return redirect(url_for('sso_login', error='2'))
    else:
        return redirect(url_for('sso_login'))
