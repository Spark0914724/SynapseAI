"""
Chat service — conversation management, OpenAI streaming, token tracking.
"""
import json
import uuid
from typing import AsyncGenerator

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import ForbiddenException, NotFoundException, QuotaExceededException
from app.models.chat import Conversation, Message
from app.models.subscription import Subscription
from app.models.token_usage import TokenUsage

client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_BASE_URL,
    default_headers={
        "HTTP-Referer": "http://localhost:5173",
        "X-Title": "SynapseAI",
    },
)

# Cost per 1k tokens (approximate, gpt-4o pricing)
COST_PER_1K = {"gpt-4o": 0.005, "gpt-4o-mini": 0.00015, "gpt-3.5-turbo": 0.0005}


# ── Conversations ──────────────────────────────────────────────────────────────

async def create_conversation(
    db: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID | None,
    model: str,
) -> Conversation:
    convo = Conversation(
        user_id=user_id,
        workspace_id=workspace_id,
        model=model,
        title="New conversation",
    )
    db.add(convo)
    await db.flush()
    return convo


async def list_conversations(
    db: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID | None = None,
) -> list[Conversation]:
    q = select(Conversation).where(Conversation.user_id == user_id)
    if workspace_id:
        q = q.where(Conversation.workspace_id == workspace_id)
    q = q.order_by(Conversation.updated_at.desc()).limit(50)
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_conversation(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Conversation:
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    convo = result.scalar_one_or_none()
    if not convo:
        raise NotFoundException("Conversation not found")
    if convo.user_id != user_id:
        raise ForbiddenException("Access denied")
    return convo


async def delete_conversation(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    convo = await get_conversation(db, conversation_id, user_id)
    await db.delete(convo)


async def get_messages(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
) -> list[Message]:
    await get_conversation(db, conversation_id, user_id)  # auth check
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    return list(result.scalars().all())


# ── Streaming chat ─────────────────────────────────────────────────────────────

async def stream_chat(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    user_content: str,
    model_override: str | None,
) -> AsyncGenerator[str, None]:
    """
    Stream an OpenAI chat completion as SSE events.
    Yields strings in the format: `data: {...}\n\n`
    Saves user + assistant messages and deducts tokens after completion.
    """
    convo = await get_conversation(db, conversation_id, user_id)
    model = model_override or convo.model or settings.OPENAI_DEFAULT_MODEL

    # Check quota
    sub_result = await db.execute(
        select(Subscription).where(Subscription.user_id == user_id)
    )
    sub = sub_result.scalar_one_or_none()
    if sub and sub.is_quota_exceeded:
        raise QuotaExceededException()

    # Fetch conversation history (last 20 messages for context window)
    history_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(20)
    )
    history = list(reversed(history_result.scalars().all()))

    # Build OpenAI messages list
    openai_messages = [
        {"role": "system", "content": (
            "You are SynapseAI, a helpful AI assistant. "
            "Be concise, accurate, and friendly."
        )}
    ]
    for msg in history:
        openai_messages.append({"role": msg.role, "content": msg.content})
    openai_messages.append({"role": "user", "content": user_content})

    # Save user message immediately
    user_msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=user_content,
        tokens_used=0,
    )
    db.add(user_msg)
    await db.flush()

    # Stream from OpenAI
    full_response = ""
    prompt_tokens = 0
    completion_tokens = 0

    try:
        stream = await client.chat.completions.create(
            model=model,
            messages=openai_messages,
            stream=True,
            stream_options={"include_usage": True},
        )

        async for chunk in stream:
            # Usage comes in the last chunk
            if chunk.usage:
                prompt_tokens = chunk.usage.prompt_tokens
                completion_tokens = chunk.usage.completion_tokens

            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta
            if delta.content:
                full_response += delta.content
                yield f"data: {json.dumps({'delta': delta.content})}\n\n"

        yield "data: [DONE]\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
        yield "data: [DONE]\n\n"
        return

    # Save assistant message
    total_tokens = prompt_tokens + completion_tokens
    assistant_msg = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=full_response,
        tokens_used=total_tokens,
    )
    db.add(assistant_msg)

    # Auto-title the conversation after first exchange
    if len(history) == 0 and full_response:
        title = user_content[:60].strip()
        if len(user_content) > 60:
            title += "…"
        convo.title = title

    # Deduct tokens from subscription quota
    if sub and total_tokens > 0:
        sub.tokens_used = min(sub.tokens_limit, sub.tokens_used + total_tokens)

    # Log token usage
    cost = (total_tokens / 1000) * COST_PER_1K.get(model, 0.005)
    usage_log = TokenUsage(
        user_id=user_id,
        workspace_id=convo.workspace_id,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        cost_usd=cost,
        endpoint="chat",
    )
    db.add(usage_log)
    await db.commit()
