import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func
from app.db.base import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = sa.Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"))
    phone_number = sa.Column(sa.Text, nullable=False)
    message_content = sa.Column(sa.Text, nullable=False)
    response_content = sa.Column(sa.Text, nullable=True)
    language = sa.Column(
        sa.Text,
        nullable=False,
        server_default='en')
    created_at = sa.Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now())
    updated_at = sa.Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now())
