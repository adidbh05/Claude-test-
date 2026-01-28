"""
Pydantic models for the Eurocode 3 Structural Design Chat API.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """Single chat message model."""
    role: MessageRole
    content: str
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., min_length=1, max_length=4000, description="User message")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str
    conversation_id: str
    timestamp: datetime
    tokens_used: Optional[int] = None


class ConversationHistory(BaseModel):
    """Model for conversation history."""
    conversation_id: str
    messages: List[ChatMessage]
    created_at: datetime
    updated_at: datetime
    title: Optional[str] = None


class ConversationSummary(BaseModel):
    """Summary model for listing conversations."""
    conversation_id: str
    title: str
    message_count: int
    created_at: datetime
    updated_at: datetime


class RateLimitInfo(BaseModel):
    """Rate limit information model."""
    requests_remaining: int
    reset_time: datetime
    limit: int


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    code: str


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    version: str
    llm_status: str
    database_status: str
