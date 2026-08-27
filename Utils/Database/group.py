from sqlalchemy import Column, Integer, Text
from Utils.Database.base import Base


class Group(Base):
    __tablename__ = 'group'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    description = Column(Text)
