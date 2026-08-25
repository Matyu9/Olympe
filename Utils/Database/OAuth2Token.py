from time import time
from sqlalchemy import Column, Integer, Text, Boolean
from Utils.Database.base import Base


class OAuth2Token(Base):
    __tablename__ = 'OAuth2Token'

    id = Column(Integer, primary_key=True)
    access_token = Column(Text)
    refresh_token = Column(Text)
    revoked = Column(Boolean, default=False)
    scope = Column(Text)

    issued_at = Column(Integer)
    expires_in = Column(Integer)

    # Référence "molle" vers Module.token / User.token, comme partout ailleurs dans ce schéma
    # (Permission.user_token, etc.) — pas de contrainte FK SQL, ces colonnes n'étant pas indexées.
    client_id = Column(Text)
    user_id = Column(Text)

    # --- Méthodes attendues par Authlib (ResourceProtector / RefreshTokenGrant) ---

    def get_scope(self):
        return self.scope or ""

    def get_expires_at(self):
        return self.issued_at + self.expires_in

    def is_expired(self):
        return self.get_expires_at() < time()

    def is_revoked(self):
        return bool(self.revoked)

    def check_client(self, client):
        return self.client_id == client.get_client_id()
