from time import time

from flask import request as flask_request
from authlib.integrations.flask_oauth2 import AuthorizationServer, ResourceProtector
from authlib.oauth2.rfc6749 import grants
from authlib.oauth2.rfc6750 import BearerTokenValidator as _BearerTokenValidator
from authlib.oauth2.rfc7636 import CodeChallenge
from authlib.oidc.core import UserInfo
from authlib.oidc.core.grants import OpenIDCode as _OpenIDCode

from Utils.Database.base import get_db
from Utils.Database.modules import Module
from Utils.Database.user import User
from Utils.Database.OAuth2AuthorizationCode import OAuth2AuthorizationCode
from Utils.Database.OAuth2Token import OAuth2Token
from Utils.OAuth.keys import get_signing_key

ACCESS_TOKEN_TTL = 3600

# Session SQLAlchemy injectée par init_oauth_server(), comme Session_SQL dans app.py
_session_factory = None


def _db():
    return get_db(_session_factory)


def _query_client(client_id):
    return _db().query(Module).filter(Module.token == client_id).first()


def _save_token(token, request):
    database = _db()
    database.add(OAuth2Token(
        access_token=token['access_token'],
        refresh_token=token.get('refresh_token'),
        scope=token['scope'],
        issued_at=int(time()),
        expires_in=token['expires_in'],
        client_id=request.client.client_id,
        user_id=request.user.token,
    ))
    database.commit()


class AuthorizationCodeGrant(grants.AuthorizationCodeGrant):
    TOKEN_ENDPOINT_AUTH_METHODS = ['client_secret_post']

    def save_authorization_code(self, code, request):
        database = _db()
        database.add(OAuth2AuthorizationCode(
            code=code,
            client_id=request.client.client_id,
            redirect_url=request.payload.redirect_uri,
            scope=request.payload.scope,
            nonce=request.payload.data.get('nonce'),
            auth_time=int(time()),
            user_id=request.user.token,
            code_challenge=request.payload.data.get('code_challenge'),
            code_challenge_method=request.payload.data.get('code_challenge_method'),
        ))
        database.commit()

    def query_authorization_code(self, code, client):
        item = _db().query(OAuth2AuthorizationCode).filter(
            OAuth2AuthorizationCode.code == code,
            OAuth2AuthorizationCode.client_id == client.client_id,
        ).first()
        if item and not item.is_expired():
            return item
        return None

    def delete_authorization_code(self, authorization_code):
        database = _db()
        database.delete(authorization_code)
        database.commit()

    def authenticate_user(self, authorization_code):
        return _db().query(User).filter(User.token == authorization_code.user_id).first()


class RefreshTokenGrant(grants.RefreshTokenGrant):
    TOKEN_ENDPOINT_AUTH_METHODS = ['client_secret_post']
    INCLUDE_NEW_REFRESH_TOKEN = True

    def authenticate_refresh_token(self, refresh_token):
        item = _db().query(OAuth2Token).filter(OAuth2Token.refresh_token == refresh_token).first()
        if item and not item.is_revoked():
            return item
        return None

    def authenticate_user(self, credential):
        return _db().query(User).filter(User.token == credential.user_id).first()

    def revoke_old_credential(self, credential):
        database = _db()
        credential.revoked = True
        database.commit()


class OpenIDCode(_OpenIDCode):
    def exists_nonce(self, nonce, request):
        exists = _db().query(OAuth2AuthorizationCode).filter(
            OAuth2AuthorizationCode.client_id == request.payload.client_id,
            OAuth2AuthorizationCode.nonce == nonce,
        ).first()
        return bool(exists)

    def get_jwt_config(self, grant, client):
        return {
            "key": get_signing_key(_db()),
            "alg": "RS256",
            "iss": flask_request.url_root.rstrip('/'),
            "exp": ACCESS_TOKEN_TTL,
        }

    def generate_user_info(self, user, scope):
        user_info = UserInfo(sub=user.token)
        if 'profile' in scope:
            user_info['preferred_username'] = user.username
        if 'email' in scope:
            user_info['email'] = user.email
            user_info['email_verified'] = bool(user.email_verified)
        return user_info


class BearerTokenValidator(_BearerTokenValidator):
    def authenticate_token(self, token_string):
        return _db().query(OAuth2Token).filter(OAuth2Token.access_token == token_string).first()


authorization_server = AuthorizationServer(query_client=_query_client, save_token=_save_token)
require_oauth = ResourceProtector()
require_oauth.register_token_validator(BearerTokenValidator())


def init_oauth_server(app, session_factory):
    global _session_factory
    _session_factory = session_factory
    authorization_server.init_app(app)
    authorization_server.register_grant(
        AuthorizationCodeGrant,
        extensions=[OpenIDCode(require_nonce=False), CodeChallenge(required=False)]
    )
    authorization_server.register_grant(RefreshTokenGrant)
