from flask import Blueprint, current_app

from Utils.Database.base import get_db
from Cogs.OAuth.authorize_cogs import oauth_authorize_cogs
from Cogs.OAuth.token_cogs import oauth_token_cogs
from Cogs.OAuth.userinfo_cogs import oauth_userinfo_cogs
from Cogs.OAuth.discovery_cogs import oidc_discovery_cogs, oidc_jwks_cogs

oauth_bp = Blueprint('oauth', __name__)


def _db():
    return get_db(current_app.config['SESSION_FACTORY'])


@oauth_bp.route('/oauth/authorize', methods=['GET', 'POST'])
def oauth_authorize():
    return oauth_authorize_cogs(_db())


@oauth_bp.route('/oauth/token', methods=['POST'])
def oauth_token():
    return oauth_token_cogs()


@oauth_bp.route('/oauth/userinfo', methods=['GET', 'POST'])
def oauth_userinfo():
    return oauth_userinfo_cogs(_db())


@oauth_bp.route('/.well-known/openid-configuration', methods=['GET'])
def openid_configuration():
    return oidc_discovery_cogs()


@oauth_bp.route('/oauth/jwks.json', methods=['GET'])
def oauth_jwks():
    return oidc_jwks_cogs(_db())
