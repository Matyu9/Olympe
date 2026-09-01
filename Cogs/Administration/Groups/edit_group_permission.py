from Utils.verify_login import login_required
from flask import request, jsonify

from Utils.Database.permission import Permission
from Utils.Database.group import Group
from Utils.Database.group_permission_override import GroupPermissionOverride

# Un groupe ne peut jamais forcer `admin` (meme risque d'escalade que pour edit_user_permission_cogs,
# a la difference que la, ce n'est meme pas verifiable par un "seul un admin peut y toucher" puisque
# n'importe quel membre du groupe en beneficierait) : whitelist volontairement sans `admin`.
GROUP_OVERRIDABLE_PERMISSION_NAMES = {
    column.name for column in Permission.__table__.columns
    if column.name not in ("id", "user_token", "admin")
}


@login_required(permission='edit_permission', redirect_endpoint='admin.show_groups')
def edit_group_permission_cogs(database):
    permission_name = request.json.get('permission_name')
    if permission_name not in GROUP_OVERRIDABLE_PERMISSION_NAMES:
        return jsonify({"error": "Permission inconnue"}), 400

    target_group = database.query(Group).filter(Group.id == request.json.get('group_id')).first()
    if target_group is None:
        return jsonify({"error": "Groupe introuvable"}), 404

    value = request.json.get('value')
    existing = database.query(GroupPermissionOverride).filter(
        GroupPermissionOverride.group_id == target_group.id,
        GroupPermissionOverride.permission_name == permission_name,
    ).first()

    if value is None:
        # Pas de valeur = retour a l'herite : on supprime l'override plutot que de stocker un None
        # (cf. choix de modelisation : absence de ligne == pas d'override).
        if existing is not None:
            database.delete(existing)
    elif existing is not None:
        existing.value = bool(value)
    else:
        database.add(GroupPermissionOverride(
            group_id=target_group.id, permission_name=permission_name, value=bool(value)
        ))
    database.commit()

    return jsonify({
        "group_id": target_group.id,
        "permission": permission_name,
        "value": value,
    })
