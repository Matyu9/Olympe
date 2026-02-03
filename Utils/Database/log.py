from sqlalchemy import Column, Integer, Text
from Utils.Database.base import Base


class Log(Base):
    __tablename__ = 'log'

    id = Column(Integer, primary_key=True)
    action_name = Column(Text)
    user_ip = Column(Text)
    user_token = Column(Text)
    details = Column(Text)
    log_level = Column(Integer)
