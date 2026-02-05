from sqlalchemy import Column, Integer, Text, Boolean
from Utils.Database.base import Base


class Module(Base):
    __tablename__ = 'modules'

    id = Column(Integer, primary_key=True)
    token = Column(Text)
    name = Column(Text)
    fqdn = Column(Text)
    client_secret = Column(Text)
    maintenance = Column(Boolean, default=False)
    status = Column(Integer, default=0)
    socket_url = Column(Text, default='/socket/')
    last_heartbeat = Column(Integer, default=0)

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