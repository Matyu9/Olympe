from flask import Blueprint, current_app

from Utils.Database.base import get_db
from Cogs.User.home import user_home_cogs
from Cogs.User.get_profile_picture import get_profile_picture_cogs
from Cogs.User.user_space import user_space_cogs
from Cogs.User.doublefa_add import doubleFA_add_cogs
from Cogs.User.email_verif import email_verif_cogs

user_bp = Blueprint('user', __name__)


@user_bp.route('/', methods=['GET'])
def home():
    return user_home_cogs(get_db(current_app.config['SESSION_FACTORY']))


@user_bp.route('/user_space/get_profile_picture')
def get_profile_picture():
    return get_profile_picture_cogs(current_app.config['UPLOAD_FOLDER'])


@user_bp.route('/user_space/', methods=['GET', 'POST'])
def user_space():
    return user_space_cogs(get_db(current_app.config['SESSION_FACTORY']), current_app.config['UPLOAD_FOLDER'])


@user_bp.route('/2FA/add/', methods=['GET', 'POST'])
def double2FA_add():
    return doubleFA_add_cogs(get_db(current_app.config['SESSION_FACTORY']))


@user_bp.route('/email/verif/', methods=['GET', 'POST'])
def email_verif():
    return email_verif_cogs(get_db(current_app.config['SESSION_FACTORY']))
