from sqlalchemy import Column, Integer, Text
from Utils.Database.base import Base


class GroupMember(Base):
    __tablename__ = 'group_member'

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, nullable=False)
    user_token = Column(Text, nullable=False)
