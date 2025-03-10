from sqlalchemy import Column, Integer, Text, Boolean
from Utils.Database.base import Base


class Module(Base):
    __tablename__ = 'modules'

    id = Column(Integer, primary_key=True)
    token = Column(Text)
    name = Column(Text)
    fqdn = Column(Text)
    maintenance = Column(Boolean, default=False)
    status = Column(Integer, default=0)
    socket_url = Column(Text, default='/socket/')
    last_heartbeat = Column(Integer, default=0)