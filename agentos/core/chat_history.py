"""Persistent Chat History Management for AgentOS"""

import json
import logging
import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ChatHistoryManager:
    """
    Persistent chat history manager with SQLite backend.
    Supports multiple conversations, context preservation, and search.
    """

    _lock = threading.Lock()

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the chat history manager.

        Args:
            db_path: Path to SQLite database file. Defaults to ~/.agentos/chat_history.db
        """
        if db_path is None:
            home = Path.home()
            agentos_dir = home / ".agentos"
            agentos_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(agentos_dir / "chat_history.db")

        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize the database schema."""
        with self._lock:
            conn = self._get_conn()
            try:
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        id TEXT PRIMARY KEY,
                        name TEXT,
                        provider TEXT,
                        model TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        metadata TEXT
                    );

                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        conversation_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        metadata TEXT,
                        FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                    );

                    CREATE INDEX IF NOT EXISTS idx_messages_conversation
                    ON messages(conversation_id);

                    CREATE INDEX IF NOT EXISTS idx_messages_timestamp
                    ON messages(timestamp);

                    CREATE INDEX IF NOT EXISTS idx_conversations_updated
                    ON conversations(updated_at);
                """)
                conn.commit()
            finally:
                conn.close()

    def create_conversation(
        self,
        conversation_id: str,
        name: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a new conversation.

        Args:
            conversation_id: Unique conversation identifier
            name: Human-readable conversation name
            provider: LLM provider used
            model: Model name
            metadata: Additional metadata

        Returns:
            The conversation ID
        """
        now = datetime.now(timezone.utc).isoformat()

        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO conversations
                    (id, name, provider, model, created_at, updated_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        conversation_id,
                        name or f"Chat {conversation_id[:8]}",
                        provider,
                        model,
                        now,
                        now,
                        json.dumps(metadata) if metadata else None,
                    ),
                )
                conn.commit()
                logger.debug(f"Created conversation: {conversation_id}")
                return conversation_id
            finally:
                conn.close()

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Add a message to a conversation.

        Args:
            conversation_id: Conversation to add message to
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Additional message metadata

        Returns:
            The message ID
        """
        now = datetime.now(timezone.utc).isoformat()

        with self._lock:
            conn = self._get_conn()
            try:
                # Ensure conversation exists
                cur = conn.execute(
                    "SELECT id FROM conversations WHERE id = ?", (conversation_id,)
                )
                if not cur.fetchone():
                    self.create_conversation(conversation_id)

                # Add message
                cur = conn.execute(
                    """
                    INSERT INTO messages
                    (conversation_id, role, content, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        conversation_id,
                        role,
                        content,
                        now,
                        json.dumps(metadata) if metadata else None,
                    ),
                )
                message_id = cur.lastrowid

                # Update conversation timestamp
                conn.execute(
                    "UPDATE conversations SET updated_at = ? WHERE id = ?",
                    (now, conversation_id),
                )

                conn.commit()
                logger.debug(
                    f"Added message {message_id} to conversation {conversation_id}"
                )
                return message_id
            finally:
                conn.close()

    def get_messages(
        self,
        conversation_id: str,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get messages from a conversation.

        Args:
            conversation_id: Conversation to get messages from
            limit: Maximum number of messages to return
            offset: Number of messages to skip

        Returns:
            List of message dictionaries
        """
        with self._lock:
            conn = self._get_conn()
            try:
                query = """
                    SELECT id, role, content, timestamp, metadata
                    FROM messages
                    WHERE conversation_id = ?
                    ORDER BY timestamp ASC
                """
                params = [conversation_id]

                if limit:
                    query += " LIMIT ? OFFSET ?"
                    params.extend([limit, offset])

                cur = conn.execute(query, params)
                messages = []
                for row in cur.fetchall():
                    msg = dict(row)
                    if msg.get("metadata"):
                        msg["metadata"] = json.loads(msg["metadata"])
                    messages.append(msg)

                return messages
            finally:
                conn.close()

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get conversation details.

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation dictionary or None if not found
        """
        with self._lock:
            conn = self._get_conn()
            try:
                cur = conn.execute(
                    "SELECT * FROM conversations WHERE id = ?",
                    (conversation_id,),
                )
                row = cur.fetchone()
                if row:
                    conv = dict(row)
                    if conv.get("metadata"):
                        conv["metadata"] = json.loads(conv["metadata"])
                    return conv
                return None
            finally:
                conn.close()

    def list_conversations(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        List all conversations, most recent first.

        Args:
            limit: Maximum number of conversations to return
            offset: Number of conversations to skip

        Returns:
            List of conversation dictionaries
        """
        with self._lock:
            conn = self._get_conn()
            try:
                cur = conn.execute(
                    """
                    SELECT c.*, COUNT(m.id) as message_count
                    FROM conversations c
                    LEFT JOIN messages m ON c.id = m.conversation_id
                    GROUP BY c.id
                    ORDER BY c.updated_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    (limit, offset),
                )
                conversations = []
                for row in cur.fetchall():
                    conv = dict(row)
                    if conv.get("metadata"):
                        conv["metadata"] = json.loads(conv["metadata"])
                    conversations.append(conv)

                return conversations
            finally:
                conn.close()

    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation and all its messages.

        Args:
            conversation_id: Conversation to delete

        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            conn = self._get_conn()
            try:
                # Delete messages first
                conn.execute(
                    "DELETE FROM messages WHERE conversation_id = ?",
                    (conversation_id,),
                )
                # Delete conversation
                cur = conn.execute(
                    "DELETE FROM conversations WHERE id = ?",
                    (conversation_id,),
                )
                conn.commit()
                deleted = cur.rowcount > 0
                if deleted:
                    logger.info(f"Deleted conversation: {conversation_id}")
                return deleted
            finally:
                conn.close()

    def clear_conversation(self, conversation_id: str) -> int:
        """
        Clear all messages from a conversation but keep the conversation.

        Args:
            conversation_id: Conversation to clear

        Returns:
            Number of messages deleted
        """
        with self._lock:
            conn = self._get_conn()
            try:
                cur = conn.execute(
                    "DELETE FROM messages WHERE conversation_id = ?",
                    (conversation_id,),
                )
                conn.commit()
                count = cur.rowcount
                logger.info(
                    f"Cleared {count} messages from conversation {conversation_id}"
                )
                return count
            finally:
                conn.close()

    def search_messages(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Search messages by content.

        Args:
            query: Search query (simple LIKE match)
            conversation_id: Optional conversation to search in
            limit: Maximum results to return

        Returns:
            List of matching messages with conversation info
        """
        with self._lock:
            conn = self._get_conn()
            try:
                if conversation_id:
                    cur = conn.execute(
                        """
                        SELECT m.*, c.name as conversation_name
                        FROM messages m
                        JOIN conversations c ON m.conversation_id = c.id
                        WHERE m.content LIKE ? AND m.conversation_id = ?
                        ORDER BY m.timestamp DESC
                        LIMIT ?
                        """,
                        (f"%{query}%", conversation_id, limit),
                    )
                else:
                    cur = conn.execute(
                        """
                        SELECT m.*, c.name as conversation_name
                        FROM messages m
                        JOIN conversations c ON m.conversation_id = c.id
                        WHERE m.content LIKE ?
                        ORDER BY m.timestamp DESC
                        LIMIT ?
                        """,
                        (f"%{query}%", limit),
                    )

                results = []
                for row in cur.fetchall():
                    msg = dict(row)
                    if msg.get("metadata"):
                        msg["metadata"] = json.loads(msg["metadata"])
                    results.append(msg)

                return results
            finally:
                conn.close()

    def get_context(
        self,
        conversation_id: str,
        max_messages: int = 20,
        max_tokens: int = 4000,
    ) -> List[Dict[str, str]]:
        """
        Get conversation context for LLM calls.
        Returns recent messages in API-compatible format.

        Args:
            conversation_id: Conversation to get context from
            max_messages: Maximum number of messages to include
            max_tokens: Approximate max tokens (based on char count / 4)

        Returns:
            List of message dicts with 'role' and 'content' keys
        """
        messages = self.get_messages(conversation_id)

        # Take recent messages
        recent = messages[-max_messages:] if len(messages) > max_messages else messages

        # Estimate tokens and trim if needed
        context = []
        total_chars = 0
        max_chars = max_tokens * 4  # Rough estimate

        for msg in reversed(recent):
            content = msg["content"]
            if total_chars + len(content) > max_chars:
                break
            context.insert(0, {"role": msg["role"], "content": content})
            total_chars += len(content)

        return context

    def export_conversation(
        self,
        conversation_id: str,
        format: str = "json",
    ) -> str:
        """
        Export a conversation to a string.

        Args:
            conversation_id: Conversation to export
            format: Export format ('json' or 'markdown')

        Returns:
            Exported conversation as string
        """
        conv = self.get_conversation(conversation_id)
        if not conv:
            return ""

        messages = self.get_messages(conversation_id)

        if format == "json":
            return json.dumps(
                {
                    "conversation": conv,
                    "messages": messages,
                },
                indent=2,
            )

        elif format == "markdown":
            lines = [
                f"# {conv.get('name', 'Conversation')}",
                f"",
                f"- **Provider:** {conv.get('provider', 'Unknown')}",
                f"- **Model:** {conv.get('model', 'Unknown')}",
                f"- **Created:** {conv.get('created_at', 'Unknown')}",
                f"",
                "---",
                "",
            ]

            for msg in messages:
                role = msg["role"].capitalize()
                content = msg["content"]
                timestamp = msg["timestamp"]
                lines.append(f"### {role} ({timestamp})")
                lines.append("")
                lines.append(content)
                lines.append("")

            return "\n".join(lines)

        return ""


# Global instance for convenience
_default_manager: Optional[ChatHistoryManager] = None


def get_chat_history_manager() -> ChatHistoryManager:
    """Get the default chat history manager instance."""
    global _default_manager
    if _default_manager is None:
        _default_manager = ChatHistoryManager()
    return _default_manager
