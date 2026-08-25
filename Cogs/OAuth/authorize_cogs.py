from flask import request, render_template, redirect, url_for

from Utils.verify_login import verify_login
from Utils.Database.user import User
from Utils.OAuth.server import authorization_server


def oauth_authorize_cogs(database):
    login_status = verify_login(database)

    if not login_status:
        next_url = request.full_path if request.query_string else request.path
        return redirect(url_for('sso_login', next=next_url))
    if login_status == 'desactivated':
        return redirect(url_for('sso_login', error='2'))

    user = database.query(User).filter(User.token == request.cookies.get('token')).first()
    grant = authorization_server.get_consent_grant(end_user=user)
    client = grant.client

    if request.method == 'GET':
        if client.require_consent:
            return render_template('SSO/oauth_consent.html', client=client, user=user,
                                   scope=grant.request.payload.scope)
        return authorization_server.create_authorization_response(grant_user=user, grant=grant)

    # POST : soumission de l'écran de consentement
    approved = request.form.get('confirm') == 'yes'
    return authorization_server.create_authorization_response(
        grant_user=user if approved else None, grant=grant)
