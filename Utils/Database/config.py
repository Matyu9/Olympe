from sqlalchemy import Column, Integer, Text
from Utils.Database.base import Base


class Config(Base):
    __tablename__ = 'config'

    id = Column(Integer, primary_key=True)
    name = Column(Text)
    content = Column(Text)


def get_config(database, name, default="0"):
    """Renvoie la valeur du réglage `name`, ou `default` si aucune ligne n'existe encore."""
    row = database.query(Config).filter(Config.name == name).first()
    return row.content if row is not None else default


def set_config(database, name, content):
    """Met à jour le réglage `name`, ou crée la ligne si elle n'existe pas encore (upsert)."""
    updated = database.query(Config).filter(Config.name == name).update({"content": content})
    if updated == 0:
        database.add(Config(name=name, content=content))