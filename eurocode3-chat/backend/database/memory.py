"""
Conversation Memory Storage using SQLite.
Provides persistent storage for chat conversations.
"""
import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
import threading


class ConversationMemory:
    """SQLite-based conversation memory storage."""

    _local = threading.local()

    def __init__(self, db_path: str = "conversations.db"):
        self.db_path = db_path
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False
            )
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection

    @contextmanager
    def _get_cursor(self):
        """Context manager for database cursor."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e

    def _init_database(self):
        """Initialize database tables."""
        with self._get_cursor() as cursor:
            # Conversations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                        ON DELETE CASCADE
                )
            """)

            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_conversation
                ON messages(conversation_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_updated
                ON conversations(updated_at DESC)
            """)

    def create_conversation(self, title: Optional[str] = None) -> str:
        """Create a new conversation and return its ID."""
        conversation_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        with self._get_cursor() as cursor:
            cursor.execute(
                """INSERT INTO conversations (id, title, created_at, updated_at)
                   VALUES (?, ?, ?, ?)""",
                (conversation_id, title or "New Conversation", now, now)
            )

        return conversation_id

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str
    ) -> int:
        """Add a message to a conversation."""
        now = datetime.utcnow().isoformat()

        with self._get_cursor() as cursor:
            # Insert message
            cursor.execute(
                """INSERT INTO messages (conversation_id, role, content, timestamp)
                   VALUES (?, ?, ?, ?)""",
                (conversation_id, role, content, now)
            )
            message_id = cursor.lastrowid

            # Update conversation timestamp
            cursor.execute(
                """UPDATE conversations SET updated_at = ? WHERE id = ?""",
                (now, conversation_id)
            )

            # Auto-generate title from first user message
            cursor.execute(
                """SELECT title FROM conversations WHERE id = ?""",
                (conversation_id,)
            )
            row = cursor.fetchone()
            if row and row['title'] == "New Conversation" and role == "user":
                # Generate title from first 50 chars of message
                title = content[:50] + ("..." if len(content) > 50 else "")
                cursor.execute(
                    """UPDATE conversations SET title = ? WHERE id = ?""",
                    (title, conversation_id)
                )

        return message_id

    def get_messages(
        self,
        conversation_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get messages from a conversation."""
        with self._get_cursor() as cursor:
            query = """
                SELECT role, content, timestamp
                FROM messages
                WHERE conversation_id = ?
                ORDER BY timestamp ASC
            """
            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query, (conversation_id,))
            rows = cursor.fetchall()

            return [
                {
                    "role": row["role"],
                    "content": row["content"],
                    "timestamp": row["timestamp"]
                }
                for row in rows
            ]

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation details."""
        with self._get_cursor() as cursor:
            cursor.execute(
                """SELECT id, title, created_at, updated_at
                   FROM conversations WHERE id = ?""",
                (conversation_id,)
            )
            row = cursor.fetchone()

            if row:
                messages = self.get_messages(conversation_id)
                return {
                    "conversation_id": row["id"],
                    "title": row["title"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "messages": messages
                }
            return None

    def list_conversations(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List all conversations with summary info."""
        with self._get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    c.id,
                    c.title,
                    c.created_at,
                    c.updated_at,
                    COUNT(m.id) as message_count
                FROM conversations c
                LEFT JOIN messages m ON c.id = m.conversation_id
                GROUP BY c.id
                ORDER BY c.updated_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))

            rows = cursor.fetchall()
            return [
                {
                    "conversation_id": row["id"],
                    "title": row["title"],
                    "message_count": row["message_count"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                }
                for row in rows
            ]

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and its messages."""
        with self._get_cursor() as cursor:
            cursor.execute(
                "DELETE FROM messages WHERE conversation_id = ?",
                (conversation_id,)
            )
            cursor.execute(
                "DELETE FROM conversations WHERE id = ?",
                (conversation_id,)
            )
            return cursor.rowcount > 0

    def update_title(self, conversation_id: str, title: str) -> bool:
        """Update conversation title."""
        with self._get_cursor() as cursor:
            cursor.execute(
                """UPDATE conversations SET title = ? WHERE id = ?""",
                (title, conversation_id)
            )
            return cursor.rowcount > 0

    def conversation_exists(self, conversation_id: str) -> bool:
        """Check if a conversation exists."""
        with self._get_cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM conversations WHERE id = ?",
                (conversation_id,)
            )
            return cursor.fetchone() is not None

    def get_context_messages(
        self,
        conversation_id: str,
        max_messages: int = 10
    ) -> List[Dict[str, str]]:
        """Get recent messages formatted for LLM context."""
        messages = self.get_messages(conversation_id)

        # Get the most recent messages for context
        recent = messages[-max_messages:] if len(messages) > max_messages else messages

        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in recent
        ]
