from Utils.verify_login import login_required
from flask import redirect, url_for, request

from Utils.Database.user import User


@login_required(permission='desactivate_account', redirect_endpoint='admin.show_user')
def desactivate_user_cogs(database):
    # Désactivation dans la base de donneés de l'utilisateur
    database.query(User).filter(User.token == request.form["token_to_desactivate"]).update(
        {"desactivated": ~User.desactivated}  # Inversion du booléen
    )
    database.commit()
    return redirect(url_for('admin.show_user', user_token=request.form['token_to_desactivate']))
