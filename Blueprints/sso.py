from flask import Blueprint, current_app

from Utils.Database.base import get_db
from Cogs.SSO.login import sso_login_cogs
from Cogs.SSO.logout import sso_logout_cogs

sso_bp = Blueprint('sso', __name__)


@sso_bp.route('/login/', methods=['GET', 'POST'])
def sso_login(error=0):
    config_data = current_app.config['CONFIG_DATA']
    return sso_login_cogs(
        get_db(current_app.config['SESSION_FACTORY']), error, config_data['modules'][0]['global_domain'],
        debug_mode=config_data['modules'][0]['debug_mode'],
    )


@sso_bp.route('/logout/', methods=['GET'])
def sso_logout():
    return sso_logout_cogs(current_app.config['CONFIG_DATA']['modules'][0]['global_domain'])
