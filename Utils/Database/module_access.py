from sqlalchemy import Column, Integer, Text
from Utils.Database.base import Base


class ModuleAccess(Base):
    """Une ligne = un accès accordé à un module, soit à un utilisateur (user_token
    renseigné), soit à un groupe (group_id renseigné). Un seul des deux doit être
    renseigné sur une même ligne."""
    __tablename__ = 'module_access'

    id = Column(Integer, primary_key=True)
    module_id = Column(Integer, nullable=False)
    user_token = Column(Text)
    group_id = Column(Integer)
