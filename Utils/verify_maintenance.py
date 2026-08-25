from flask import request, render_template, redirect, url_for
from Utils.verify_login import verify_login
from Utils.Database.permission import Permission

def verify_maintenance(database, maintenance):
    # /oauth/ et /.well-known/ gèrent leur propre auth (session pour /oauth/authorize avec reprise via
    # ?next=, client_secret ou Bearer token pour les appels serveur-à-serveur des modules) : le hook
    # générique ne doit pas s'interposer.
    exempt_prefixes = ('/static/', '/sso/', '/user_space/get_profile_picture', '/oauth/', '/.well-known/')
    if not request.path.startswith(exempt_prefixes):
        if not verify_login(database):
            return redirect(url_for('sso_login', error='0'))
        else:
            user_permission = database.query(Permission).filter(Permission.user_token == request.cookies.get('token')).first()
            if maintenance and not user_permission[0]:
                return render_template("User/maintenance.html")
            elif maintenance and user_permission[0]:
                return None
            else:
                return None
    else:
        return None
