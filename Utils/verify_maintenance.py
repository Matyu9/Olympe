from flask import request, render_template, redirect, url_for
from Utils.verify_login import verify_login
from Utils.Database.permission import Permission

def verify_maintenance(database, maintenance):
    # /oauth/, /.well-known/ et /api/ gèrent leur propre auth (session pour /oauth/authorize avec
    # reprise via ?next=, client_secret/Bearer token pour les appels serveur-à-serveur des modules,
    # identifiants dans le corps JSON pour /api/sso/login) : le hook générique ne doit pas
    # s'interposer, sinon un client externe sans cookie Olympe préalable ne peut jamais les appeler.
    exempt_prefixes = ('/static/', '/sso/', '/user_space/get_profile_picture', '/oauth/', '/.well-known/', '/api/')
    if not request.path.startswith(exempt_prefixes):
        if not verify_login(database):
            return redirect(url_for('sso.sso_login', error='0'))
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
