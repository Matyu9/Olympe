from sqlalchemy import Column, Integer, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from Utils.Database.base import Base


class OAuth2AuthorizationCode(Base):
    __tablename__ = 'OAuth2Code'

    id = Column(Integer, primary_key=True)
    code = Column(Text, unique=True, nullable=False)

    client_id = Column(Text, foreign_key='modules.token', ondelete='CASCADE')
    user_id = Column(Text, foreign_key='user.token', ondelete='CASCADE')

    redirect_url = Column(Text)
    scope = Column(Text)
    auth_time = Column(Integer)
