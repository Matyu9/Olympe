from flask import Blueprint, current_app

from Utils.Database.base import get_db
from Cogs.Administration.User.show_user import show_user_cogs
from Cogs.Administration.User.desactivate_user import desactivate_user_cogs
from Cogs.Administration.User.delete_user import delete_user_cogs
from Cogs.Administration.User.add_user import add_user_cogs
from Cogs.Administration.User.edit_user_permission import edit_user_permission_cogs
from Cogs.Administration.User.global_permission import global_permission_cogs
from Cogs.Administration.User.smtp_config import smtp_config_cogs
from Cogs.Administration.User.smtp_test import smtp_test_cogs
from Cogs.Administration.Modules.show_modules import show_modules_cogs
from Cogs.Administration.Modules.add_modules import add_modules_cogs
from Cogs.Administration.Modules.maintenance import maintenance_cogs
from Cogs.Administration.Modules.regenerate_secret import regenerate_secret_cogs
from Cogs.Administration.Modules.show_install_form import show_install_form_cogs
from Cogs.Administration.Modules.start_install import start_install_cogs
from Cogs.Administration.Modules.show_install_progress import show_install_progress_cogs
from Cogs.Administration.Modules.module_access import (
    toggle_restricted_access_cogs, grant_module_access_cogs, revoke_module_access_cogs
)
from Cogs.Administration.Groups.show_groups import show_groups_cogs
from Cogs.Administration.Groups.add_group import add_group_cogs
from Cogs.Administration.Groups.delete_group import delete_group_cogs
from Cogs.Administration.Groups.edit_group_members import add_group_member_cogs, remove_group_member_cogs

admin_bp = Blueprint('admin', __name__)


def _db():
    return get_db(current_app.config['SESSION_FACTORY'])


@admin_bp.route('/user/', methods=['GET', 'POST'])
def show_user():
    return show_user_cogs(_db(), current_app.config['UPLOAD_FOLDER'])


@admin_bp.route('/user/add/', methods=['GET', 'POST'])
def add_user():
    return add_user_cogs(_db())


@admin_bp.route('/user/edit_permission/', methods=['POST'])
def edit_permission_user():
    return edit_user_permission_cogs(_db())


@admin_bp.route('/user/desactivate/', methods=['POST'])
def desactivate_user():
    return desactivate_user_cogs(_db())


@admin_bp.route('/user/delete/', methods=['POST'])
def delete_user():
    return delete_user_cogs(_db())


@admin_bp.route('/permission/global/', methods=['POST', 'GET'])
def global_permission():
    return global_permission_cogs(_db())


@admin_bp.route('/modules/', methods=['POST', 'GET'])
def show_modules():
    return show_modules_cogs(_db())


@admin_bp.route('/modules/add/', methods=['POST', 'GET'])
def add_modules():
    return add_modules_cogs(_db())


@admin_bp.route('/modules/maintenance/', methods=['POST'])
def maintenance():
    return maintenance_cogs(_db())


@admin_bp.route('/modules/regenerate_secret/', methods=['POST'])
def regenerate_secret():
    return regenerate_secret_cogs(_db())


@admin_bp.route('/modules/access/toggle_restricted/', methods=['POST'])
def toggle_restricted_access():
    return toggle_restricted_access_cogs(_db())


@admin_bp.route('/modules/access/grant/', methods=['POST'])
def grant_module_access():
    return grant_module_access_cogs(_db())


@admin_bp.route('/modules/access/revoke/', methods=['POST'])
def revoke_module_access():
    return revoke_module_access_cogs(_db())


@admin_bp.route('/groups/', methods=['GET', 'POST'])
def show_groups():
    return show_groups_cogs(_db())


@admin_bp.route('/groups/add/', methods=['GET', 'POST'])
def add_group():
    return add_group_cogs(_db())


@admin_bp.route('/groups/delete/', methods=['POST'])
def delete_group():
    return delete_group_cogs(_db())


@admin_bp.route('/groups/members/add/', methods=['POST'])
def add_group_member():
    return add_group_member_cogs(_db())


@admin_bp.route('/groups/members/remove/', methods=['POST'])
def remove_group_member():
    return remove_group_member_cogs(_db())


@admin_bp.route('/modules/install/', methods=['GET'])
def show_install_form():
    return show_install_form_cogs(_db())


@admin_bp.route('/modules/install/start/', methods=['POST'])
def start_install():
    return start_install_cogs(_db(), current_app.config['SOCKETIO'], current_app.config['SESSION_FACTORY'])


@admin_bp.route('/modules/install/<int:installation_id>/', methods=['GET'])
def show_install_progress(installation_id):
    return show_install_progress_cogs(_db(), installation_id)


@admin_bp.route('/smtp/config/', methods=['POST', 'GET'])
def smtp_config():
    return smtp_config_cogs(_db())


@admin_bp.route('/smtp/config/test', methods=['POST'])
def smtp_test():
    return smtp_test_cogs(_db())
