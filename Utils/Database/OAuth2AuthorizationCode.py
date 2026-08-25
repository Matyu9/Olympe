from time import time
from sqlalchemy import Column, Integer, Text
from Utils.Database.base import Base

# Durée de vie d'un code d'autorisation, en secondes (recommandation OIDC : 10 minutes max)
AUTH_CODE_TTL = 300


class OAuth2AuthorizationCode(Base):
    __tablename__ = 'OAuth2Code'

    id = Column(Integer, primary_key=True)
    code = Column(Text, unique=True, nullable=False)

    # Référence "molle" vers Module.token / User.token, comme partout ailleurs dans ce schéma
    # (Permission.user_token, etc.) — pas de contrainte FK SQL, ces colonnes n'étant pas indexées.
    client_id = Column(Text)
    user_id = Column(Text)

    redirect_url = Column(Text)
    scope = Column(Text)
    nonce = Column(Text)
    auth_time = Column(Integer)
    code_challenge = Column(Text)
    code_challenge_method = Column(Text)

    # --- Méthodes attendues par Authlib (AuthorizationCodeGrant) ---

    def get_redirect_uri(self):
        return self.redirect_url

    def get_scope(self):
        return self.scope or ""

    def get_auth_time(self):
        return self.auth_time

    def get_nonce(self):
        return self.nonce

    def get_acr(self):
        return None

    def get_amr(self):
        return None

    def is_expired(self):
        return self.auth_time + AUTH_CODE_TTL < time()
