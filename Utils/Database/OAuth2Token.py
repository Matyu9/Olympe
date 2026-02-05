from sqlalchemy import Column, Integer, Text, Boolean, ForeignKey
from Utils.Database.base import Base


class OAuth2Token(Base):
    __tablename__ = 'OAuth2Token'

    id = Column(Integer, primary_key=True)
    access_token = Column(Text)
    refresh_token = Column(Text)
    revoked = Column(Boolean, default=False)
    scope = Column(Text)

    issued_at = Column(Integer)
    expires_in = Column(Integer)

    client_id = Column(Text, foreign_key='modules.token', ondelete='CASCADE')
    user_id = Column(Text, foreign_key='user.token', ondelete='CASCADE')
