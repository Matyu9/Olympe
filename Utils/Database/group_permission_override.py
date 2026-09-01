from sqlalchemy import Column, Integer, Text, Boolean, UniqueConstraint
from Utils.Database.base import Base


class GroupPermissionOverride(Base):
    __tablename__ = 'group_permission_override'
    __table_args__ = (UniqueConstraint('group_id', 'permission_name'),)

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, nullable=False)
    permission_name = Column(Text, nullable=False)
    value = Column(Boolean, nullable=False)
