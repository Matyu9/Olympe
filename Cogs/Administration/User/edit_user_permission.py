from Utils.verify_login import login_required
from flask import request, jsonify

from Utils.Database.permission import Permission
from Utils.permission_resolution import get_effective_permission_view

# Whitelist des colonnes réellement modifiables : empêche d'injecter un nom de colonne
# arbitraire (ex: une colonne SQLAlchemy interne) via `permission_name`.
EDITABLE_PERMISSION_NAMES = {
    column.name for column in Permission.__table__.columns
    if column.name not in ("id", "user_token")
}


@login_required(permission='edit_permission', redirect_endpoint='admin.show_user')
def edit_user_permission_cogs(database):
    # On récupère les permissions effectives de l'utilisateur (droit personnel éventuellement forcé
    # par un groupe, cf. Utils/permission_resolution.py)
    user_permission = get_effective_permission_view(database, request.cookies.get('token'))

    permission_name = request.json.get('permission_name')
    if permission_name not in EDITABLE_PERMISSION_NAMES:
        return jsonify({"error": "Permission inconnue"}), 400

    # Seul un admin peut accorder/retirer le droit `admin` lui-même : sinon un compte
    # n'ayant que `edit_permission` pourrait s'auto-élever en admin.
    if permission_name == 'admin' and not user_permission.admin:
        return jsonify({"error": "Permission refusée"}), 403

    database.query(Permission).filter(Permission.user_token == request.json["token"]).update(
        {
            permission_name: bool(request.json['value']),
        }
    )
    database.commit()

    return jsonify({
        "token": request.cookies.get("token"),
        "permission": permission_name,
        "value": request.json['value']
    })