from sqlalchemy import Column, Integer, Text
from Utils.Database.base import Base


class Group(Base):
    __tablename__ = 'group'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    description = Column(Text)
    # Rang utilisé pour départager les overrides de permission quand un utilisateur appartient
    # à plusieurs groupes en conflit sur le même droit (cf. Utils/permission_resolution.py) :
    # priorité la plus haute gagne, égalité tranchée par False.
    priority = Column(Integer, nullable=False, default=0)
