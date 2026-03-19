"""
Qdrant Memory Client with Sentence Transformers
================================================
Handles conversation memory and real embeddings using local sentence-transformers.
"""

from typing import List, Optional, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
    Filter,
    PointIdsList,
    FieldCondition,
    MatchValue,
)
from sentence_transformers import SentenceTransformer
import uuid
from datetime import datetime


class MemoryClient:
    """Qdrant-based memory client with sentence-transformer embeddings."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "dr_ikechukwu_pa",
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        """
        Initialize the memory client.
        
        Args:
            host: Qdrant host
            port: Qdrant port
            collection_name: Collection name
            embedding_model: Sentence transformer model name
        """
        self.client: QdrantClient = QdrantClient(host=host, port=port)
        self.collection_name = collection_name
        self.embedding_model = SentenceTransformer(embedding_model)
        self._ensure_collection()
    
    def _ensure_collection(self) -> None:
        """Ensure the collection exists, create if not."""
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if self.collection_name not in collection_names:
            embedding_size = self.embedding_model.get_sentence_embedding_dimension()
            if embedding_size is None:
                raise ValueError("Failed to get embedding dimension from model")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=embedding_size,
                    distance=Distance.COSINE,
                ),
            )
    
    def add_memory(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """
        Add a memory to the vector store.
        
        Args:
            text: Text to embed and store
            metadata: Optional metadata
            session_id: Optional session ID for grouping
        
        Returns:
            Memory ID
        """
        memory_id = str(uuid.uuid4())
        vector = self.embedding_model.encode(text).tolist()
        
        payload = {
            "text": text,
            "created_at": datetime.utcnow().isoformat(),
            **(metadata or {}),
        }
        
        if session_id:
            payload["session_id"] = session_id
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=memory_id,
                    vector=vector,
                    payload=payload,
                )
            ],
        )
        
        return memory_id
    
    def search(
        self,
        query: str,
        limit: int = 5,
        session_id: Optional[str] = None,
        filter_conditions: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar memories.
        
        Args:
            query: Query text
            limit: Maximum results
            session_id: Optional session filter
            filter_conditions: Optional filter conditions
        
        Returns:
            List of similar memories with scores
        """
        query_vector = self.embedding_model.encode(query).tolist()
        
        must_filters: List[FieldCondition] = []
        if session_id:
            must_filters.append(FieldCondition(key="session_id", match=MatchValue(value=session_id)))
        
        if filter_conditions:
            for key, value in filter_conditions.items():
                must_filters.append(FieldCondition(key=key, match=MatchValue(value=value)))
        
        query_filter = Filter(must=must_filters) if must_filters else None  # type: ignore[arg-type]
        
        results = self.client.query_points(  # type: ignore[attr-defined]
            collection_name=self.collection_name,
            query=query_vector,
            limit=limit,
            query_filter=query_filter,
        )
        
        return [
            {
                "id": result.id,
                "text": result.payload.get("text") if result.payload else "",
                "score": result.score,
                "metadata": {k: v for k, v in (result.payload or {}).items() if k != "text"},
            }
            for result in results.points
        ]
    
    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all memories for a session.
        
        Args:
            session_id: Session ID
        
        Returns:
            List of session memories
        """
        session_filter = Filter(must=[FieldCondition(key="session_id", match=MatchValue(value=session_id))])
        results, _ = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=session_filter,
            limit=100,
        )
        
        return [
            {
                "id": result.id,
                "text": result.payload.get("text") if result.payload else "",
                "created_at": result.payload.get("created_at") if result.payload else None,
                "metadata": {k: v for k, v in (result.payload or {}).items() if k not in ["text", "created_at"]},
            }
            for result in results
        ]
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete all memories for a session.
        
        Args:
            session_id: Session ID
        
        Returns:
            Whether deletion was successful
        """
        try:
            session_filter = Filter(must=[FieldCondition(key="session_id", match=MatchValue(value=session_id))])
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=session_filter,
            )
            return True
        except Exception:
            return False
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a specific memory.
        
        Args:
            memory_id: Memory ID
        
        Returns:
            Whether deletion was successful
        """
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=PointIdsList(points=[memory_id]),
            )
            return True
        except Exception:
            return False
    
    def get_collections(self) -> List[str]:
        """
        Get all collection names.
        
        Returns:
            List of collection names
        """
        collections = self.client.get_collections().collections
        return [c.name for c in collections]
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check health of the memory service.
        
        Returns:
            Health status
        """
        try:
            collections = self.client.get_collections()
            return {
                "status": "healthy",
                "collections": len(collections.collections),
                "current_collection": self.collection_name,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }


# Global memory client instance
_memory_client: Optional[MemoryClient] = None
_memory_client_init_error: Optional[str] = None


def get_memory_client() -> Optional[MemoryClient]:
    """Get or create the global memory client. Returns None if unavailable."""
    global _memory_client, _memory_client_init_error
    
    if _memory_client_init_error:
        # Already tried and failed - return None
        return None
    
    if _memory_client is None:
        try:
            from .config import app_config
            _memory_client = MemoryClient(
                host=app_config.qdrant_host,
                port=app_config.qdrant_port,
                collection_name=app_config.qdrant_collection,
            )
        except Exception as e:
            _memory_client_init_error = str(e)
            import structlog
            logger = structlog.get_logger()
            logger.warning("memory_client_init_failed", error=_memory_client_init_error)
            return None
    
    return _memory_client


__all__ = [
    "MemoryClient",
    "get_memory_client",
]