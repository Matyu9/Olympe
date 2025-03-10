from sqlalchemy import Column, Integer, Text
from Utils.Database.base import Base


class Config(Base):
    __tablename__ = 'config'

    id = Column(Integer, primary_key=True)
    name = Column(Text)
    content = Column(Text)