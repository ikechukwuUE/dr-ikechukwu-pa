"""
Conversation Manager with Redis + Qdrant
========================================
Per-domain conversational memory with:
- Short-term: Redis (fast, ephemeral per session)
- Long-term: Qdrant (semantic search across sessions)
"""

from typing import List, Dict, Any, Optional
import json
import redis
import structlog
from datetime import datetime
from pydantic import BaseModel

from .memory import MemoryClient
from .config import app_config

logger = structlog.get_logger()


class ConversationTurn(BaseModel):
    """Single conversation turn."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None


class ConversationManager:
    """
    Unified conversation manager with:
    - Short-term memory (Redis): Last N messages per session
    - Long-term memory (Qdrant): Semantic recall across sessions
    """
    
    # Domain-specific TTL in Redis (24 hours default)
    DOMAIN_TTL = {
        "cds": 86400,       # 24 hours - medical context important
        "finance": 86400,    # 24 hours - financial context important
        "fashion": 43200,   # 12 hours - style preferences
        "aidev": 43200,     # 12 hours - code context
    }
    
    # Max short-term messages to keep per domain
    MAX_SHORT_TERM = 10
    
    def __init__(self, memory_client: Optional[MemoryClient] = None):
        """
        Initialize conversation manager.
        
        Args:
            memory_client: Optional Qdrant client for long-term memory
        """
        # Redis for short-term memory
        self.redis = redis.from_url(
            app_config.redis_url,
            decode_responses=True
        )
        
        # Qdrant for long-term memory (reuse existing)
        self.memory_client = memory_client
    
    def _get_redis_key(self, domain: str, session_id: str) -> str:
        """Generate Redis key for conversation history."""
        return f"conversation:{domain}:{session_id}"
    
    def _get_user_key(self, domain: str, user_id: str) -> str:
        """Generate Redis key for user preferences."""
        return f"user:{domain}:{user_id}"
    
    def add_turn(
        self,
        domain: str,
        session_id: str,
        user_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a conversation turn to both short and long-term memory.
        
        Args:
            domain: Domain (cds, finance, fashion, aidev)
            session_id: Current session ID
            user_id: User ID for persistent identity
            role: "user" or "assistant"
            content: Message content
            metadata: Optional metadata
        """
        turn = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }
        
        # 1. Add to Redis (short-term)
        redis_key = self._get_redis_key(domain, session_id)
        try:
            # Append to list
            self.redis.rpush(redis_key, json.dumps(turn))
            # Trim to max size
            self.redis.ltrim(
                redis_key,
                -self.MAX_SHORT_TERM,
                -1
            )
            # Set TTL
            ttl = self.DOMAIN_TTL.get(domain, 86400)
            self.redis.expire(redis_key, ttl)
        except redis.RedisError as e:
            logger.warning("redis_add_failed", error=str(e))
        
        # 2. Add to Qdrant (long-term semantic memory)
        if self.memory_client:
            try:
                context = f"{role.upper()}: {content}"
                self.memory_client.add_memory(
                    text=context,
                    metadata={
                        "domain": domain,
                        "session_id": session_id,
                        "user_id": user_id,
                        "role": role,
                        "timestamp": turn["timestamp"],
                    },
                    session_id=f"{domain}:{user_id}"  # Cross-session for same user/domain
                )
            except Exception as e:
                logger.warning("qdrant_add_failed", error=str(e))
        
        logger.info(
            "conversation_turn_added",
            domain=domain,
            session_id=session_id,
            user_id=user_id,
            role=role
        )
    
    def get_short_term_context(
        self,
        domain: str,
        session_id: str,
        max_turns: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Get recent conversation turns from Redis.
        
        Args:
            domain: Domain
            session_id: Session ID
            max_turns: Number of recent turns to retrieve
            
        Returns:
            List of conversation turns
        """
        redis_key = self._get_redis_key(domain, session_id)
        
        try:
            # Get last N items - redis-py type stubs issue
            turns_data = self.redis.lrange(redis_key, -max_turns, -1)  # type: ignore[assignment]
            if not turns_data:
                return []
            return [json.loads(str(turn)) for turn in turns_data]  # type: ignore[iterable]
        except (redis.RedisError, json.JSONDecodeError, TypeError) as e:
            logger.warning("redis_get_failed", error=str(e))
            return []
    
    def get_long_term_context(
        self,
        domain: str,
        user_id: str,
        query: str,
        limit: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Get semantically similar past conversations from Qdrant.
        
        Args:
            domain: Domain
            user_id: User ID
            query: Query to search for
            limit: Max results
            
        Returns:
            List of relevant past conversations
        """
        if not self.memory_client:
            return []
        
        try:
            # Search with user/domain filter
            results = self.memory_client.search(
                query=query,
                limit=limit,
                session_id=f"{domain}:{user_id}",  # Cross-session
                filter_conditions={
                    "domain": domain,
                }
            )
            return results
        except Exception as e:
            logger.warning("qdrant_search_failed", error=str(e))
            return []
    
    def get_full_context(
        self,
        domain: str,
        session_id: str,
        user_id: str,
        current_query: str,
        short_term_limit: int = 5,
        long_term_limit: int = 3,
    ) -> Dict[str, Any]:
        """
        Get complete context: recent + semantic recall.
        
        Args:
            domain: Domain
            session_id: Current session
            user_id: User ID
            current_query: Current user query for semantic search
            short_term_limit: Recent turns
            long_term_limit: Semantic recall limit
            
        Returns:
            Dict with short_term and long_term context
        """
        # Get recent conversation
        # Get recent conversation
        short_term = self.get_short_term_context(
            domain, session_id, short_term_limit
        )
        
        # Get semantic recall
        # Get semantic recall
        long_term = self.get_long_term_context(
            domain, user_id, current_query, long_term_limit
        )
        
        return {
            "short_term": short_term,
            "long_term": long_term,
            "has_history": len(short_term) > 0,
        }
    
    def save_user_preference(
        self,
        domain: str,
        user_id: str,
        key: str,
        value: Any,
    ) -> None:
        """
        Save user preference (e.g., favorite styles, medical conditions).
        
        Args:
            domain: Domain
            user_id: User ID
            key: Preference key
            value: Preference value
        """
        user_key = self._get_user_key(domain, user_id)
        
        try:
            self.redis.hset(user_key, key, json.dumps(value))
            self.redis.expire(user_key, 30 * 86400)  # 30 days
        except redis.RedisError as e:
            logger.warning("redis_preference_save_failed", error=str(e))
    
    def get_user_preferences(
        self,
        domain: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Get all user preferences for a domain.
        
        Args:
            domain: Domain
            user_id: User ID
            
        Returns:
            Dict of preferences
        """
        user_key = self._get_user_key(domain, user_id)
        
        try:
            # Get preferences - redis-py type stubs issue
            prefs_raw = self.redis.hgetall(user_key)  # type: ignore[assignment]
            if not prefs_raw:
                return {}
            prefs_dict: Dict[str, str] = {}
            for k, v in prefs_raw.items():  # type: ignore[union-attr]
                prefs_dict[str(k)] = str(v)
            return {k: json.loads(v) for k, v in prefs_dict.items()}
        except (redis.RedisError, json.JSONDecodeError, TypeError) as e:
            logger.warning("redis_preferences_get_failed", error=str(e))
            return {}
    
    def clear_session(self, domain: str, session_id: str) -> None:
        """
        Clear short-term memory for a session.
        
        Args:
            domain: Domain
            session_id: Session ID
        """
        redis_key = self._get_redis_key(domain, session_id)
        try:
            self.redis.delete(redis_key)
        except redis.RedisError as e:
            logger.warning("redis_clear_failed", error=str(e))


# Global instance
_conversation_manager: Optional[ConversationManager] = None


def get_conversation_manager() -> ConversationManager:
    """Get or create the conversation manager."""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
    return _conversation_manager


__all__ = [
    "ConversationManager",
    "ConversationTurn",
    "get_conversation_manager",
]
