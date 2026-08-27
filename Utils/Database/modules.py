from sqlalchemy import Column, Integer, Text, Boolean
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHash
from Utils.Database.base import Base

# Scopes OIDC pris en charge par Olympe pour l'instant
ALLOWED_SCOPES = {"openid", "profile", "email"}


class Module(Base):
    __tablename__ = 'modules'

    id = Column(Integer, primary_key=True)
    token = Column(Text)
    name = Column(Text)
    fqdn = Column(Text)
    client_secret = Column(Text)  # Hash argon2, jamais stocké en clair (cf. User.password)
    require_consent = Column(Boolean, default=False)
    maintenance = Column(Boolean, default=False)
    status = Column(Integer, default=0)
    socket_url = Column(Text, default='/socket/')
    last_heartbeat = Column(Integer, default=0)
    restricted_access = Column(Boolean, default=False)

    @property
    def client_id(self):
        return self.token

    @property
    def redirect_uris(self):
        # On construit l'URL de callback automatiquement
        # Si fqdn = "https://wiki.cantina.org", ça renvoie ["https://wiki.cantina.org/callback"]
        # Attention : Assure-toi que le fqdn n'a pas de slash à la fin dans ta BDD
        clean_fqdn = self.fqdn.rstrip('/')
        return [f"{clean_fqdn}/callback"]

    # --- Méthodes attendues par Authlib (AuthorizationServer) ---

    def get_client_id(self):
        return self.client_id

    def get_default_redirect_uri(self):
        return self.redirect_uris[0]

    def get_allowed_scope(self, scope):
        if not scope:
            return ""
        requested = set(scope.split())
        return " ".join(sorted(requested & ALLOWED_SCOPES))

    def check_redirect_uri(self, redirect_uri):
        return redirect_uri in self.redirect_uris

    def check_client_secret(self, client_secret):
        if not self.client_secret:
            return False
        try:
            return PasswordHasher().verify(self.client_secret, client_secret)
        except (VerifyMismatchError, InvalidHash):
            return False

    def check_endpoint_auth_method(self, method, endpoint):
        # Un seul mode pris en charge : le module envoie client_id + client_secret dans le corps de la requête
        if endpoint == 'token':
            return method == 'client_secret_post'
        return True

    def check_response_type(self, response_type):
        return response_type == 'code'

    def check_grant_type(self, grant_type):
        return grant_type in ('authorization_code', 'refresh_token')