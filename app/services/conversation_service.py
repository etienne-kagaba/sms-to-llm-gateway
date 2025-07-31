from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models import Conversation
from typing import Optional, List
from datetime import timedelta, datetime, timezone


async def save_conversation(
    db: AsyncSession,
    phone_number: str,
    message_content: str,
    response_content: Optional[str],
    language: str = "en"
) -> Conversation:
    now = datetime.now(timezone.utc)

    conversation = Conversation(
        phone_number=phone_number,
        message_content=message_content,
        response_content=response_content,
        language=language,
        created_at=now,
        updated_at=now,
    )

    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation


async def get_recent_conversations(
    db: AsyncSession,
    phone_number: str,
    hours: int = 48
) -> List[Conversation]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    stmt = (
        select(Conversation)
        .where(Conversation.phone_number == phone_number)
        .where(Conversation.created_at >= cutoff)
        .order_by(Conversation.created_at.asc())
    )
    result = await db.execute(stmt)
    conversations = result.scalars().all()
    return conversations
