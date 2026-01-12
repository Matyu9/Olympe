from flask import Flask, g
from flask_socketio import SocketIO
from os import path, getcwd
from json import load

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from Utils.Database.base import Base, get_db

from Utils.verify_maintenance import verify_maintenance

from Cogs.SSO.login import sso_login_cogs
from Cogs.SSO.logout import sso_logout_cogs
from Cogs.User.home import user_home_cogs
from Cogs.User.get_profile_picture import get_profile_picture_cogs
from Cogs.User.user_space import user_space_cogs
from Cogs.User.doublefa_add import doubleFA_add_cogs
from Cogs.User.email_verif import email_verif_cogs
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

from Cogs.API.SSO.login_cogs import api_login_cogs
from Cogs.API.User.user_info_cogs import api_user_info_cogs

from Cogs.Socket.heart_beat_cogs import heart_beat_cogs
from Cogs.Socket.ping_server_socket_cogs import ping_server_socket_cogs

file_path = path.abspath(path.join(getcwd(), "config.json"))  # Trouver le chemin complet du fichier config.json

# Lecture du fichier JSON
with open(file_path, 'r') as file:
    config_data = load(file)  # Ouverture du fichier config.json

app = Flask(__name__)  # Création de l'application Flask
app.config['SECRET_KEY'] = config_data['modules'][0]['secret_key']
socketio = SocketIO(app, cors_allowed_origins="*")  # Lien entre l'application Flaks et le WebSocket
app.config['UPLOAD_FOLDER'] = path.abspath(path.join(getcwd(), "static/ProfilePicture/"))


engine_sql = create_engine(
    f"mysql+pymysql://{config_data['database'][0]['username']}:{config_data['database'][0]['password']}@{config_data['database'][0]['address']}:{config_data['database'][0]['port']}/", #{config_data['database'][0]['name']}
    pool_size=20,        # Max 10 connexions en parallèle
    max_overflow=40,      # 20 connexions supplémentaires si besoin
    pool_timeout=30,     # Temps max d’attente pour une connexion libre
    pool_recycle=1800    # Ferme et recrée une connexion après 30 min
)

Base.metadata.create_all(engine_sql)

Session_SQL = sessionmaker(bind=engine_sql)


# Vérifiacation du mode de maintenance
@app.before_request
def before_req():
    return verify_maintenance(get_db(Session_SQL), config_data['modules'][0]['maintenance'])

# Destruction des sessions de DB en fin de req
@app.teardown_appcontext
def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()  # Ferme proprement la connexion pour éviter les fuites


@app.route('/', methods=['GET'])
def home():
    return user_home_cogs(get_db(Session_SQL))


@app.route('/user_space/get_profile_picture')
def get_profile_picture():
    return get_profile_picture_cogs(app.config['UPLOAD_FOLDER'])


@app.route('/user_space/', methods=['GET', 'POST'])
def user_space():
    return user_space_cogs(get_db(Session_SQL), app.config['UPLOAD_FOLDER'])


@app.route('/2FA/add/', methods=['GET', 'POST'])
def double2FA_add():
    return doubleFA_add_cogs(get_db(Session_SQL))


@app.route('/email/verif/', methods=['GET', 'POST'])
def email_verif():
    return email_verif_cogs(get_db(Session_SQL))


"""
    Partie administration
"""


@app.route('/admin/user/', methods=['GET', 'POST'])
def show_user():
    return show_user_cogs(get_db(Session_SQL), app.config['UPLOAD_FOLDER'])


@app.route('/admin/user/add/', methods=['GET', 'POST'])
def add_user():
    return add_user_cogs(get_db(Session_SQL))


@app.route('/admin/user/edit_permission/', methods=['POST'])
def edit_permission_user():
    return edit_user_permission_cogs(get_db(Session_SQL))


@app.route('/admin/user/desactivate/', methods=['POST'])
def desactivate_user():
    return desactivate_user_cogs(get_db(Session_SQL))


@app.route('/admin/user/delete/', methods=['POST'])
def delete_user():
    return delete_user_cogs(get_db(Session_SQL))


@app.route('/admin/permission/global/', methods=['POST', 'GET'])
def global_permission():
    return global_permission_cogs(get_db(Session_SQL))


@app.route('/admin/modules/', methods=['POST', 'GET'])
def show_modules():
    return show_modules_cogs(get_db(Session_SQL))


@app.route('/admin/modules/add/', methods=['POST', 'GET'])
def add_modules():
    return add_modules_cogs(get_db(Session_SQL))


@app.route('/admin/modules/maintenance/', methods=['POST'])
def maintenance():
    from Cogs.Administration.Modules.maintenance import maintenance_cogs
    return maintenance_cogs(get_db(Session_SQL))


@app.route('/admin/smtp/config/', methods=['POST', 'GET'])
def smtp_config():
    return smtp_config_cogs(get_db(Session_SQL))


@app.route('/admin/smtp/config/test', methods=['POST'])
def smtp_test():
    return smtp_test_cogs(get_db(Session_SQL))


"""
    Partie Single Sign On
"""


@app.route('/sso/login/', methods=['GET', 'POST'])
def sso_login(error=0):
    return sso_login_cogs(get_db(Session_SQL), error, config_data['modules'][0]['global_domain'],
                          config_data['modules'][0]["secret_key"])

@app.route('/sso/logout/', methods=['GET'])
def sso_logout():
    return sso_logout_cogs()

"""
    Partie Socket
"""

@socketio.on('heartbeat')
def heart_beat(data):
    return heart_beat_cogs(data, get_db(Session_SQL))

@socketio.on('ping_server')
def ping_server_socket():
    return ping_server_socket_cogs()

"""
    Partie API
"""

@app.route('/api/sso/login', methods=['POST'])
def api_sso_login(error=0):
    return api_login_cogs(get_db(Session_SQL), error)


@app.route('/api/user/info/<token>', methods=['get'])
def api_user_info(error=0):
    return api_user_info_cogs(get_db(Session_SQL), error)

if __name__ == '__main__':
    socketio.run(app,
                 allow_unsafe_werkzeug=True,
                 debug=config_data["modules"][0]["debug_mode"],
                 port=config_data["modules"][0]["port"]
                 )

