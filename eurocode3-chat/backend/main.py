"""
Eurocode 3 Structural Design Chat Application
FastAPI Backend Server

A specialized chatbot for steel structural design according to EN 1993.
"""
import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, status, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates

from app.models import (
    ChatRequest,
    ChatResponse,
    ConversationHistory,
    ConversationSummary,
    ErrorResponse,
    HealthResponse,
    RateLimitInfo
)
from database.memory import ConversationMemory
from services.llm_service import LLMService, MockLLMService, LLMServiceError
from middleware.rate_limiter import RateLimitMiddleware, RateLimiter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
USE_MOCK_LLM = os.getenv("USE_MOCK_LLM", "true").lower() == "true"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))
RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", "500"))
DB_PATH = os.getenv("DB_PATH", "conversations.db")

# Initialize services
memory = ConversationMemory(db_path=DB_PATH)
rate_limiter = RateLimiter(
    requests_per_minute=RATE_LIMIT_PER_MINUTE,
    requests_per_hour=RATE_LIMIT_PER_HOUR
)

# Initialize LLM service
if USE_MOCK_LLM:
    llm_service = MockLLMService()
    logger.info("Using Mock LLM Service for development")
else:
    llm_service = LLMService(provider=LLM_PROVIDER)
    logger.info(f"Using {LLM_PROVIDER} LLM Service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Eurocode 3 Chat Application...")
    yield
    logger.info("Shutting down Eurocode 3 Chat Application...")


# Create FastAPI app
app = FastAPI(
    title="Eurocode 3 Structural Design Chat",
    description="""
    An AI-powered chat application specialized in steel structural design
    according to Eurocode 3 (EN 1993).

    ## Features
    - Expert knowledge of EN 1993-1-1 through EN 1993-1-12
    - Cross-section classification and resistance calculations
    - Buckling analysis (flexural, lateral-torsional)
    - Connection design (bolted and welded)
    - Step-by-step calculations with clause references

    ## Rate Limits
    - 30 requests per minute
    - 500 requests per hour
    """,
    version="1.0.0",
    lifespan=lifespan,
    responses={
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    rate_limiter=rate_limiter,
    exclude_paths=["/", "/health", "/docs", "/openapi.json", "/redoc", "/static"]
)

# Mount static files
STATIC_PATH = os.path.join(os.path.dirname(__file__), "../frontend/static")
TEMPLATES_PATH = os.path.join(os.path.dirname(__file__), "../frontend/templates")

if os.path.exists(STATIC_PATH):
    app.mount("/static", StaticFiles(directory=STATIC_PATH), name="static")

templates = Jinja2Templates(directory=TEMPLATES_PATH) if os.path.exists(TEMPLATES_PATH) else None


# ============== Routes ==============

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root(request: Request):
    """Serve the main frontend page."""
    if templates:
        return templates.TemplateResponse("index.html", {"request": request})
    return HTMLResponse(content="<h1>Eurocode 3 Chat API</h1><p>Visit /docs for API documentation</p>")


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Check the health status of all services."""
    llm_healthy = await llm_service.health_check()
    db_healthy = True

    try:
        memory.list_conversations(limit=1)
    except Exception:
        db_healthy = False

    overall_status = "healthy" if (llm_healthy and db_healthy) else "degraded"

    return HealthResponse(
        status=overall_status,
        version="1.0.0",
        llm_status="healthy" if llm_healthy else "unavailable",
        database_status="healthy" if db_healthy else "unavailable"
    )


@app.post(
    "/api/chat",
    response_model=ChatResponse,
    tags=["Chat"],
    responses={
        400: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def chat(request: ChatRequest):
    """
    Send a message and receive an AI response.

    The AI assistant specializes in Eurocode 3 steel design calculations,
    providing step-by-step solutions with proper clause references.

    - **message**: Your question or design problem
    - **conversation_id**: Optional ID to continue an existing conversation
    """
    try:
        # Get or create conversation
        if request.conversation_id:
            if not memory.conversation_exists(request.conversation_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Conversation not found"
                )
            conversation_id = request.conversation_id
        else:
            conversation_id = memory.create_conversation()

        # Store user message
        memory.add_message(conversation_id, "user", request.message)

        # Get conversation context
        context_messages = memory.get_context_messages(conversation_id, max_messages=10)

        # Generate response
        result = await llm_service.generate_response(context_messages)

        # Store assistant response
        memory.add_message(conversation_id, "assistant", result["content"])

        return ChatResponse(
            response=result["content"],
            conversation_id=conversation_id,
            timestamp=datetime.utcnow(),
            tokens_used=result.get("tokens_used")
        )

    except LLMServiceError as e:
        logger.error(f"LLM service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@app.get(
    "/api/conversations",
    response_model=list[ConversationSummary],
    tags=["Conversations"]
)
async def list_conversations(limit: int = 50, offset: int = 0):
    """
    List all conversations with summary information.

    - **limit**: Maximum number of conversations to return (default: 50)
    - **offset**: Number of conversations to skip (default: 0)
    """
    conversations = memory.list_conversations(limit=limit, offset=offset)
    return [
        ConversationSummary(
            conversation_id=c["conversation_id"],
            title=c["title"],
            message_count=c["message_count"],
            created_at=datetime.fromisoformat(c["created_at"]),
            updated_at=datetime.fromisoformat(c["updated_at"])
        )
        for c in conversations
    ]


@app.get(
    "/api/conversations/{conversation_id}",
    response_model=ConversationHistory,
    tags=["Conversations"],
    responses={404: {"model": ErrorResponse}}
)
async def get_conversation(conversation_id: str):
    """
    Get full conversation history including all messages.

    - **conversation_id**: The unique identifier of the conversation
    """
    conversation = memory.get_conversation(conversation_id)

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    return ConversationHistory(
        conversation_id=conversation["conversation_id"],
        title=conversation.get("title"),
        messages=conversation["messages"],
        created_at=datetime.fromisoformat(conversation["created_at"]),
        updated_at=datetime.fromisoformat(conversation["updated_at"])
    )


@app.delete(
    "/api/conversations/{conversation_id}",
    tags=["Conversations"],
    responses={404: {"model": ErrorResponse}}
)
async def delete_conversation(conversation_id: str):
    """
    Delete a conversation and all its messages.

    - **conversation_id**: The unique identifier of the conversation
    """
    if not memory.delete_conversation(conversation_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    return {"message": "Conversation deleted successfully"}


@app.patch(
    "/api/conversations/{conversation_id}/title",
    tags=["Conversations"],
    responses={404: {"model": ErrorResponse}}
)
async def update_conversation_title(conversation_id: str, title: str):
    """
    Update the title of a conversation.

    - **conversation_id**: The unique identifier of the conversation
    - **title**: The new title for the conversation
    """
    if not memory.update_title(conversation_id, title):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    return {"message": "Title updated successfully"}


@app.get("/api/rate-limit", response_model=RateLimitInfo, tags=["System"])
async def get_rate_limit_info(request: Request):
    """Get current rate limit status for your IP."""
    _, info = await rate_limiter.is_allowed(request)

    return RateLimitInfo(
        requests_remaining=info.get("minute_remaining", 0),
        reset_time=datetime.utcnow(),
        limit=rate_limiter.requests_per_minute
    )


# Run with: uvicorn main:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
