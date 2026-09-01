from flask import Blueprint, current_app

from Utils.Database.base import get_db
from Cogs.API.SSO.login_cogs import api_login_cogs

api_bp = Blueprint('api', __name__)


@api_bp.route('/sso/login', methods=['POST'])
def api_sso_login(error=0):
    return api_login_cogs(get_db(current_app.config['SESSION_FACTORY']), error)
