from flask import jsonify, url_for

from Utils.OAuth.keys import get_jwks


def oidc_discovery_cogs():
    return jsonify({
        "issuer": url_for('user.home', _external=True).rstrip('/'),
        "authorization_endpoint": url_for('oauth.oauth_authorize', _external=True),
        "token_endpoint": url_for('oauth.oauth_token', _external=True),
        "userinfo_endpoint": url_for('oauth.oauth_userinfo', _external=True),
        "jwks_uri": url_for('oauth.oauth_jwks', _external=True),
        "response_types_supported": ["code"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"],
        "scopes_supported": ["openid", "profile", "email"],
        "token_endpoint_auth_methods_supported": ["client_secret_post"],
        "claims_supported": ["sub", "preferred_username", "email", "email_verified"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
    })


def oidc_jwks_cogs(database):
    return jsonify(get_jwks(database))
