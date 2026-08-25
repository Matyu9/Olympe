from flask import jsonify

from Utils.Database.user import User
from Utils.OAuth.server import require_oauth


def oauth_userinfo_cogs(database):
    with require_oauth.acquire('openid') as token:
        user = database.query(User).filter(User.token == token.user_id).first()
        scope = token.get_scope().split()

        claims = {"sub": user.token}
        if "profile" in scope:
            claims["preferred_username"] = user.username
        if "email" in scope:
            claims["email"] = user.email
            claims["email_verified"] = bool(user.email_verified)

        return jsonify(claims)
