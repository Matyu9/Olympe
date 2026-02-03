from sqlalchemy import Column, Integer, Boolean, Date, Text
from Utils.Database.base import Base

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    token = Column(Text, nullable=False)
    username = Column(Text, nullable=False)
    password = Column(Text, nullable=False)
    email = Column(Text, nullable=False)
    email_verified = Column(Boolean, default=False)
    email_verification_code = Column(Text)
    picture = Column(Boolean, default=False)
    A2F = Column(Boolean, default=False)
    A2F_secret = Column(Text)
    last_connection = Column(Date)
    desactivated = Column(Boolean, default=False)
    theme = Column(Text, default='light')
    super_admin = Column(Boolean, default=False)
