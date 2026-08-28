from Utils.verify_login import verify_login
from flask import redirect, url_for, request, jsonify

from Utils.Database.permission import Permission

# Whitelist des colonnes réellement modifiables : empêche d'injecter un nom de colonne
# arbitraire (ex: une colonne SQLAlchemy interne) via `permission_name`.
EDITABLE_PERMISSION_NAMES = {
    column.name for column in Permission.__table__.columns
    if column.name not in ("id", "user_token")
}


def edit_user_permission_cogs(database):
    # Vérification de si l'utilisateur est bien connecté et n'a pas un compte désactivé
    if verify_login(database) and verify_login(database) != 'desactivated':
        # On récupère les permissions de l'utilisateur afin de pouvoir afficher les options qui correspondent
        user_permission = database.query(Permission).filter(Permission.user_token == request.cookies.get('token')).first()
        if not user_permission.edit_permission and not user_permission.admin:
            return redirect(url_for('show_user'))

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

    elif verify_login(database) == "desactivated":
        return redirect(url_for('sso_login', error='2'))
    else:
        return redirect(url_for('sso_login'))