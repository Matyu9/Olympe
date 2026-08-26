from flask import Flask, g
from flask_socketio import SocketIO, join_room
from os import path, getcwd, environ
from json import load
from secrets import token_hex

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from Utils.Database.base import Base, get_db
from Utils.Database.config import Config
# Import nécessaire pour que Base.metadata connaisse ces tables (sinon create_all ne les crée pas)
from Utils.Database.OAuth2AuthorizationCode import OAuth2AuthorizationCode
from Utils.Database.OAuth2Token import OAuth2Token
from Utils.Database.module_installation import ModuleInstallation

from Utils.verify_maintenance import verify_maintenance
from Utils.OAuth.server import init_oauth_server

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
from Cogs.Administration.Modules.maintenance import maintenance_cogs
from Cogs.Administration.Modules.regenerate_secret import regenerate_secret_cogs
from Cogs.Administration.Modules.show_install_form import show_install_form_cogs
from Cogs.Administration.Modules.start_install import start_install_cogs
from Cogs.Administration.Modules.show_install_progress import show_install_progress_cogs

from Cogs.API.SSO.login_cogs import api_login_cogs
from Cogs.API.User.user_info_cogs import api_user_info_cogs

from Cogs.Socket.heart_beat_cogs import heart_beat_cogs
from Cogs.Socket.ping_server_socket_cogs import ping_server_socket_cogs

from Cogs.OAuth.authorize_cogs import oauth_authorize_cogs
from Cogs.OAuth.token_cogs import oauth_token_cogs
from Cogs.OAuth.userinfo_cogs import oauth_userinfo_cogs
from Cogs.OAuth.discovery_cogs import oidc_discovery_cogs, oidc_jwks_cogs


def create_app(config_path=None):
    """Construit et retourne (app, socketio). Regroupe ce qui était exécuté au niveau du
    module pour permettre de recréer une instance (tests, config différente) sans réimporter
    le fichier. Limite connue : Utils/OAuth/server.py garde un état global (authorization_server,
    _session_factory) partagé par toutes les instances créées via cette fonction."""

    file_path = config_path or path.abspath(path.join(getcwd(), "config.json"))  # Trouver le chemin complet du fichier config.json

    # Lecture du fichier JSON
    with open(file_path, 'r') as file:
        config_data = load(file)  # Ouverture du fichier config.json

    app = Flask(__name__)  # Création de l'application Flask
    app.config['SECRET_KEY'] = config_data['modules'][0]['secret_key']
    socketio = SocketIO(app, cors_allowed_origins="*")  # Lien entre l'application Flaks et le WebSocket
    app.config['UPLOAD_FOLDER'] = path.abspath(path.join(getcwd(), "static/ProfilePicture/"))
    # Exposés via app.config pour que les Cogs y accèdent avec flask.current_app plutôt
    # qu'en réimportant ce module (ce qui créait un import circulaire, cf. maintenance.py)
    app.config['CONFIG_DATA'] = config_data
    app.config['CONFIG_FILE_PATH'] = file_path

    engine_sql = create_engine(
        f"mysql+pymysql://{config_data['database'][0]['username']}:{config_data['database'][0]['password']}@{config_data['database'][0]['address']}:{config_data['database'][0]['port']}/", #{config_data['database'][0]['name']}
        pool_size=20,        # Max 10 connexions en parallèle
        max_overflow=40,      # 20 connexions supplémentaires si besoin
        pool_timeout=30,     # Temps max d'attente pour une connexion libre
        pool_recycle=1800    # Ferme et recrée une connexion après 30 min
    )

    Base.metadata.create_all(engine_sql)

    Session_SQL = sessionmaker(bind=engine_sql)

    # Génération du secret partagé utilisé par les modules Cantina pour valider une session Olympe (cf. cantinaUtils)
    with Session_SQL() as _startup_db:
        if _startup_db.query(Config).filter(Config.name == "secret_token").scalar() is None:
            _startup_db.add(Config(name="secret_token", content=token_hex(32)))
            _startup_db.commit()

    # Mise en place du serveur OIDC (endpoints /oauth/*)
    if config_data["modules"][0]["debug_mode"]:
        # Autorise le protocole OIDC en HTTP pour le développement local uniquement
        environ["AUTHLIB_INSECURE_TRANSPORT"] = "1"
    app.config["OAUTH2_REFRESH_TOKEN_GENERATOR"] = True
    # expires_in du access_token, quel que soit le grant qui l'a émis (le refresh_token, lui, n'expire
    # pas tant qu'il n'est pas révoqué : pas de champ d'expiration dédié dans OAuth2Token pour l'instant)
    app.config["OAUTH2_TOKEN_EXPIRES_IN"] = {"authorization_code": 3600, "refresh_token": 3600}
    init_oauth_server(app, Session_SQL)

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
        return maintenance_cogs(get_db(Session_SQL))

    @app.route('/admin/modules/regenerate_secret/', methods=['POST'])
    def regenerate_secret():
        return regenerate_secret_cogs(get_db(Session_SQL))

    @app.route('/admin/modules/install/', methods=['GET'])
    def show_install_form():
        return show_install_form_cogs(get_db(Session_SQL))

    @app.route('/admin/modules/install/start/', methods=['POST'])
    def start_install():
        return start_install_cogs(get_db(Session_SQL), socketio, Session_SQL)

    @app.route('/admin/modules/install/<int:installation_id>/', methods=['GET'])
    def show_install_progress(installation_id):
        return show_install_progress_cogs(get_db(Session_SQL), installation_id)

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
        return sso_login_cogs(get_db(Session_SQL), error, config_data['modules'][0]['global_domain'])

    @app.route('/sso/logout/', methods=['GET'])
    def sso_logout():
        return sso_logout_cogs()

    """
        Partie OIDC
    """

    @app.route('/oauth/authorize', methods=['GET', 'POST'])
    def oauth_authorize():
        return oauth_authorize_cogs(get_db(Session_SQL))

    @app.route('/oauth/token', methods=['POST'])
    def oauth_token():
        return oauth_token_cogs()

    @app.route('/oauth/userinfo', methods=['GET', 'POST'])
    def oauth_userinfo():
        return oauth_userinfo_cogs(get_db(Session_SQL))

    @app.route('/.well-known/openid-configuration', methods=['GET'])
    def openid_configuration():
        return oidc_discovery_cogs()

    @app.route('/oauth/jwks.json', methods=['GET'])
    def oauth_jwks():
        return oidc_jwks_cogs(get_db(Session_SQL))

    """
        Partie Socket
    """

    @socketio.on('heartbeat')
    def heart_beat(data):
        return heart_beat_cogs(data, get_db(Session_SQL))

    @socketio.on('join_install_room')
    def join_install(data):
        join_room(str(data['installation_id']))

    @socketio.on('ping_server')
    def ping_server_socket():
        return ping_server_socket_cogs()

    """
        Partie API
    """

    @app.route('/api/sso/login', methods=['POST'])
    def api_sso_login(error=0):
        return api_login_cogs(get_db(Session_SQL), error)

    @app.route('/api/user/info/<token>', methods=['GET'])
    def api_user_info(error=0):
        return api_user_info_cogs(get_db(Session_SQL), error)

    return app, socketio


app, socketio = create_app()

if __name__ == '__main__':
    socketio.run(app,
                 allow_unsafe_werkzeug=True,
                 debug=app.config['CONFIG_DATA']["modules"][0]["debug_mode"],
                 port=app.config['CONFIG_DATA']["modules"][0]["port"]
                 )
