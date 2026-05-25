import uuid
from pydantic import BaseModel
from datetime import datetime


class ConversationCreate(BaseModel):
    workspace_id: uuid.UUID | None = None
    model: str = "gpt-4o"


class ConversationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    workspace_id: uuid.UUID | None
    title: str
    model: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    tokens_used: int
    created_at: datetime

    model_config = {"from_attributes": True}


class SendMessageRequest(BaseModel):
    content: str
    model: str | None = None   # override per-message if needed
