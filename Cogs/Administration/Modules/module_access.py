from Utils.verify_login import login_required
from flask import request, jsonify

from Utils.Database.user import User
from Utils.Database.modules import Module
from Utils.Database.group import Group
from Utils.Database.module_access import ModuleAccess


@login_required(permission='on_off_modules', redirect_endpoint='admin.show_modules')
def toggle_restricted_access_cogs(database):
    module = database.query(Module).filter(Module.token == request.json['module_token']).first()
    if module is None:
        return jsonify({"success": False}), 404

    database.query(Module).filter(Module.token == module.token).update(
        {"restricted_access": not module.restricted_access}
    )
    database.commit()

    return jsonify({"success": True, "restricted_access": not module.restricted_access})


@login_required(permission='on_off_modules', redirect_endpoint='admin.show_modules')
def grant_module_access_cogs(database):
    module = database.query(Module).filter(Module.token == request.json['module_token']).first()
    if module is None:
        return jsonify({"success": False, "error": "module introuvable"}), 404

    subject_type = request.json['subject_type']
    subject_value = request.json['subject_value']

    if subject_type == 'user':
        target_user = database.query(User).filter(User.username == subject_value).first()
        if target_user is None:
            return jsonify({"success": False, "error": "utilisateur introuvable"}), 404
        existing = database.query(ModuleAccess).filter(
            ModuleAccess.module_id == module.id, ModuleAccess.user_token == target_user.token
        ).first()
        if existing is None:
            database.add(ModuleAccess(module_id=module.id, user_token=target_user.token))
            database.commit()

    elif subject_type == 'group':
        target_group = database.query(Group).filter(Group.id == int(subject_value)).first()
        if target_group is None:
            return jsonify({"success": False, "error": "groupe introuvable"}), 404
        existing = database.query(ModuleAccess).filter(
            ModuleAccess.module_id == module.id, ModuleAccess.group_id == target_group.id
        ).first()
        if existing is None:
            database.add(ModuleAccess(module_id=module.id, group_id=target_group.id))
            database.commit()
    else:
        return jsonify({"success": False, "error": "subject_type invalide"}), 400

    return jsonify({"success": True})


@login_required(permission='on_off_modules', redirect_endpoint='admin.show_modules')
def revoke_module_access_cogs(database):
    database.query(ModuleAccess).filter(ModuleAccess.id == request.json['access_id']).delete()
    database.commit()

    return jsonify({"success": True})
