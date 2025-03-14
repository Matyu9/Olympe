from Utils.verify_login import verify_login
from flask import redirect, url_for, request, jsonify

from Utils.Database.permission import Permission


def edit_user_permission_cogs(database):
    # Vérification de si l'utilisateur est bien connecté et n'a pas un compte désactivé
    if verify_login(database) and verify_login(database) != 'desactivated':
        # On récupère les permissions de l'utilisateur afin de pouvoir afficher les options qui correspondent
        user_permission = database.query(Permission).filter(Permission.user_token == request.cookies.get('token')).first()
        if not user_permission.edit_permission and not user_permission.admin:
            return redirect(url_for('show_user'))

        print({
                request.json['permission_name']: request.json['value'],
            })

        database.query(Permission).filter(Permission.user_token == request.json["token"]).update(
            {
                request.json['permission_name']: request.json['value'],
            }
        )
        database.commit()

        return jsonify({
            "token": request.cookies.get("token"),
            "permission": request.json['permission_name'],
            "value": request.json['value']
        })

    elif verify_login(database) == "desactivated":
        return redirect(url_for('sso_login', error='2'))
    else:
        return redirect(url_for('sso_login'))