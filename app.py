import sys
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
from Utils.Database.group import Group
from Utils.Database.group_member import GroupMember
from Utils.Database.module_access import ModuleAccess

from Utils.verify_maintenance import verify_maintenance
from Utils.OAuth.server import init_oauth_server

from Blueprints.user import user_bp
from Blueprints.administration import admin_bp
from Blueprints.sso import sso_bp
from Blueprints.oauth import oauth_bp
from Blueprints.api import api_bp

from Cogs.Socket.heart_beat_cogs import heart_beat_cogs
from Cogs.Socket.ping_server_socket_cogs import ping_server_socket_cogs


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
    # Exposés via app.config pour que les Blueprints y accèdent avec flask.current_app
    # plutôt que par closure (cf. commentaire CONFIG_DATA ci-dessus)
    app.config['SESSION_FACTORY'] = Session_SQL
    app.config['SOCKETIO'] = socketio

    # Génération du secret partagé utilisé par les modules Cantina pour valider une session Olympe (cf. cantinaUtils)
    with Session_SQL() as _startup_db:
        if _startup_db.query(Config).filter(Config.name == "secret_token").scalar() is None:
            _startup_db.add(Config(name="secret_token", content=token_hex(32)))
            _startup_db.commit()

    # Mise en place du serveur OIDC (endpoints /oauth/*)
    if config_data["modules"][0]["debug_mode"]:
        # Autorise le protocole OIDC en HTTP pour le développement local uniquement
        environ["AUTHLIB_INSECURE_TRANSPORT"] = "1"

        # Garde-fou : debug_mode désactive la vérification TLS d'OIDC (ligne ci-dessus) et active
        # le débogueur Flask (exécution de code arbitraire si son endpoint est exposé). C'est
        # normal en dev local (global_domain sur 127.0.0.1/localhost), mais si ce n'est pas le
        # cas, ce déploiement est probablement joignable depuis l'extérieur avec ces protections
        # désactivées — on prévient bruyamment plutôt que de laisser passer silencieusement.
        global_domain = config_data['modules'][0].get('global_domain', '')
        domain_host = global_domain.split(':')[0].lower()
        if domain_host not in ('127.0.0.1', 'localhost'):
            print('\n'.join([
                '!' * 78,
                '! ATTENTION : debug_mode=true avec global_domain="{}" (pas localhost).'.format(global_domain),
                '! Ce mode desactive la verification TLS d\'OIDC et active le debogueur Flask',
                '! (execution de code arbitraire si son endpoint est expose sur le reseau).',
                '! Ne JAMAIS utiliser debug_mode=true en dehors d\'un environnement de dev local.',
                '!' * 78,
            ]), file=sys.stderr)
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

    # Chaque blueprint regroupe les routes d'un domaine (mirroir de Cogs/<Domaine>/) ;
    # les vues y accèdent à la DB/socketio/config via flask.current_app.config plutôt
    # que par closure sur les variables locales de create_app (cf. SESSION_FACTORY ci-dessus).
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(sso_bp, url_prefix='/sso')
    app.register_blueprint(oauth_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

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

    return app, socketio


app, socketio = create_app()

if __name__ == '__main__':
    socketio.run(app,
                 allow_unsafe_werkzeug=True,
                 debug=app.config['CONFIG_DATA']["modules"][0]["debug_mode"],
                 port=app.config['CONFIG_DATA']["modules"][0]["port"]
                 )
