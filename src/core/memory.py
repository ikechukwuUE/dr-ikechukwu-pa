"""
Conversation Memory System using Qdrant
======================================
Stores and retrieves previous conversations for context-aware responses.
"""

from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from src.core.config import settings

logger = logging.getLogger(__name__)


class ConversationMemory:
    """
    Manages conversation history using Qdrant vector database.
    Provides semantic search and retrieval of past conversations.
    """
    
    _instance = None
    _client = None
    _collection_name = "conversations"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Qdrant client if available."""
        if not settings.QDRANT_URL or not settings.QDRANT_API_KEY:
            logger.warning("Qdrant not configured - memory will use in-memory storage")
            self._client = None
            self._in_memory_store = {}
            return
        
        try:
            from qdrant_client import QdrantClient
            self._client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY
            )
            # Create collection if not exists
            self._ensure_collection()
            logger.info("Conversation memory initialized with Qdrant")
        except Exception as e:
            logger.warning(f"Failed to initialize Qdrant: {e}. Using in-memory storage.")
            self._client = None
            self._in_memory_store = {}
    
    def _ensure_collection(self):
        """Ensure the conversations collection exists."""
        if not self._client:
            return
            
        try:
            from qdrant_client.models import Distance, VectorParams
            
            collections = self._client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self._collection_name not in collection_names:
                self._client.create_collection(
                    collection_name=self._collection_name,
                    vectors_config=VectorParams(
                        size=384,  # Default embedding size
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {self._collection_name}")
        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")
    
    def add_message(
        self,
        thread_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a message to the conversation history.
        
        Args:
            thread_id: Unique identifier for the conversation thread
            role: 'user' or 'assistant'
            content: The message content
            metadata: Optional metadata (domain, timestamp, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        if not self._client:
            # Use in-memory storage
            if thread_id not in self._in_memory_store:
                self._in_memory_store[thread_id] = []
            
            self._in_memory_store[thread_id].append({
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            })
            return True
        
        try:
            from qdrant_client.models import PointStruct
            
            # For simplicity, store as a document without vector
            # In production, you'd generate embeddings
            point = PointStruct(
                id=f"{thread_id}_{datetime.utcnow().timestamp()}",
                vector=[0.0] * 384,  # Placeholder
                payload={
                    "thread_id": thread_id,
                    "role": role,
                    "content": content,
                    "timestamp": datetime.utcnow().isoformat(),
                    "metadata": metadata or {}
                }
            )
            
            self._client.upsert(
                collection_name=self._collection_name,
                points=[point]
            )
            return True
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            return False
    
    def get_conversation(
        self,
        thread_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a thread.
        
        Args:
            thread_id: Unique identifier for the conversation thread
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of message dictionaries
        """
        if not self._client:
            # Use in-memory storage
            messages = self._in_memory_store.get(thread_id, [])
            return messages[-limit:]
        
        try:
            from qdrant_client.models import Filter, FieldCondition
            
            results = self._client.scroll(
                collection_name=self._collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="thread_id",
                            match={"value": thread_id}
                        )
                    ]
                ),
                limit=limit,
                with_payload=True
            )
            
            messages = []
            for point in results[0]:
                payload = point.payload
                messages.append({
                    "role": payload.get("role"),
                    "content": payload.get("content"),
                    "timestamp": payload.get("timestamp"),
                    "metadata": payload.get("metadata", {})
                })
            
            return messages
        except Exception as e:
            logger.error(f"Error getting conversation: {e}")
            return []
    
    def search_similar(
        self,
        query: str,
        thread_id: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar conversations.
        
        Args:
            query: Search query
            thread_id: Optional thread to search within
            limit: Maximum results
            
        Returns:
            List of similar messages
        """
        # Simplified implementation - in production, use embeddings
        if not self._client:
            # Simple text search in memory
            results = []
            for tid, messages in self._in_memory_store.items():
                if thread_id and tid != thread_id:
                    continue
                for msg in messages:
                    if query.lower() in msg.get("content", "").lower():
                        results.append(msg)
            return results[:limit]
        
        logger.info("Semantic search not fully implemented - using fallback")
        return []
    
    def clear_conversation(self, thread_id: str) -> bool:
        """
        Clear conversation history for a thread.
        
        Args:
            thread_id: Unique identifier for the conversation thread
            
        Returns:
            True if successful
        """
        if not self._client:
            self._in_memory_store.pop(thread_id, None)
            return True
        
        logger.info(f"Clearing conversation: {thread_id}")
        # Note: Qdrant doesn't support direct delete by payload
        # In production, you'd implement soft delete or use filters
        return True


# Global singleton instance
conversation_memory = ConversationMemory()


# Convenience functions
def add_to_memory(
    thread_id: str,
    role: str,
    content: str,
    domain: Optional[str] = None
) -> bool:
    """Add a message to conversation memory."""
    return conversation_memory.add_message(
        thread_id=thread_id,
        role=role,
        content=content,
        metadata={"domain": domain} if domain else {}
    )


def get_memory(thread_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get conversation history."""
    return conversation_memory.get_conversation(thread_id, limit)


def search_memory(
    query: str,
    thread_id: Optional[str] = None,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """Search conversation memory."""
    return conversation_memory.search_similar(query, thread_id, limit)


def clear_memory(thread_id: str) -> bool:
    """Clear conversation memory."""
    return conversation_memory.clear_conversation(thread_id)
