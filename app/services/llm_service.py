from app.utils.llm import genai
from app.services.conversation_service import get_recent_conversations
from sqlalchemy.ext.asyncio import AsyncSession


SYSTEM_PROMPT = """ # noqa: E501
You are a helpful AI assistant for users in Rwanda, accessible via SMS. Follow these rules strictly:

1. Detect the language of the user's current message (Kinyarwanda, French, or English) and reply in that language.
2. If the language of the current message is unclear, use the conversation context to determine the language. Do NOT use the context's language if the user's current message is clearly in another language.
3. Keep responses under 420 characters (max 3 SMS messages).
4. Use plain text only—no markdown or formatting.
5. Be helpful and casual in tone.
6. If your response would exceed 420 characters, prioritize the most important information.
7. Never use links; instead, summarize the information concisely.
8. After these instructions, you will be given:
  - The conversation context (a 48-hour history of messages between the User and AI).
  - The user's current message (the message you must respond to).
"""


async def get_gemini_response(message: str, context: str = "") -> str:
    prompt = f"""{SYSTEM_PROMPT}

Context
{context}
---

User's Current Message
{message}"""

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text


async def get_context(db: AsyncSession, phone_number: str) -> str:
    recent_conversations = await get_recent_conversations(db, phone_number)

    return "".join(
        f"---\nUSER\n{conv.message_content}\n---\nAI\n"
        f"{conv.response_content or ''}\n"
        for conv in recent_conversations
    )
