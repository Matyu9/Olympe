from flask import request, render_template, redirect, url_for
from Utils.verify_login import verify_login
from Utils.Database.permission import Permission

def verify_maintenance(database, maintenance):
    if not request.path.startswith('/static/') and not request.path.startswith('/sso/') and not request.path.startswith('/user_space/get_profile_picture'):
        if not verify_login(database):
            return redirect(url_for('sso_login', error='0'))
        else:
            user_permission = database.query(Permission).filter(Permission.user_token == request.cookies.get('token')).first()
            if maintenance and not user_permission[0]:
                return render_template("User/maintenance.html")
            elif maintenance and user_permission[0]:
                pass
            else:
                pass
    else:
        pass
