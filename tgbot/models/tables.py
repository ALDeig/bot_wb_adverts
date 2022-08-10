import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from tgbot.services.db_connection import Base


class User(Base):
    __tablename__ = "users"
    id = sa.Column(sa.BigInteger, primary_key=True, index=True)
    username = sa.Column(sa.String(), nullable=True)
    subscribe = sa.Column(sa.Date(), nullable=True)
    tracking_id = relationship("Tracking")


class Tracking(Base):
    __tablename__ = "tracking"
    tracking_id = sa.Column(UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))
    user_id = sa.Column(sa.ForeignKey("users.id", ondelete="CASCADE"))
    query_text = sa.Column(sa.String, unique=False, nullable=True)
    scu = sa.Column(sa.Integer, unique=False, nullable=True)


class PromoCode(Base):
    __tablename__ = "promo_code"
    code = sa.Column(sa.String, primary_key=True)
    user = sa.Column(sa.ForeignKey("users.id", ondelete="CASCADE"))
    amount_use = sa.Column(sa.Integer)
    discount_size = sa.Column(sa.Integer)
