from Utils.verify_login import login_required
from flask import redirect, url_for, request

from Utils.Database.permission import Permission
from Utils.Database.user import User


@login_required(permission='delete_account', redirect_endpoint='admin.show_user')
def delete_user_cogs(database):
    # Suppressions des permissions et des données de l'utilisateur.
    database.query(Permission).filter(Permission.user_token == request.form["token_to_delete"]).delete()
    database.query(User).filter(User.token == request.form["token_to_delete"]).delete()
    database.commit()

    return redirect(url_for('admin.show_user'))
