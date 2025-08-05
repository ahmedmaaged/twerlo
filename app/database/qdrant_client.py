from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from qdrant_client.http import models
from app.config import settings
from typing import List, Dict, Any, Optional
import uuid
import time

class QdrantDB:
    client: QdrantClient = None
    collection_name: str = settings.qdrant_collection_name

qdrant_db = QdrantDB()

async def get_qdrant_client():
    return qdrant_db.client

def connect_to_qdrant():
    """Create Qdrant connection"""
    qdrant_db.client = QdrantClient(
        url=settings.qdrant_url,
        prefer_grpc=False,
        https=True,
        port=None,
        timeout=30.0  # Increased timeout for Railway
    )

    print(f"Connected to Qdrant at: {settings.qdrant_url}")

def close_qdrant_connection():
    """Close Qdrant connection"""
    if qdrant_db.client:
        qdrant_db.client.close()
        print("Disconnected from Qdrant")

def ensure_collection_exists():
    """Ensure collection exists, create if needed"""
    try:
        collections = qdrant_db.client.get_collections()
        collection_names = [col.name for col in collections.collections]
        
        if qdrant_db.collection_name not in collection_names:
            from app.config import settings
            qdrant_db.client.create_collection(
                collection_name=qdrant_db.collection_name,
                vectors_config=VectorParams(
                    size=settings.embedding_dimensions,
                    distance=Distance.COSINE
                )
            )
    except Exception as e:
        print(f"Failed to ensure collection exists: {e}")
        raise

def store_embeddings(
    embeddings: List[float],
    text_chunk: str,
    metadata: Dict[str, Any]
) -> str:
    """Store embeddings in Qdrant"""
    try:
        # Ensure collection exists before storing
        ensure_collection_exists()
        
        point_id = str(uuid.uuid4())
        
        # Prepare payload with metadata
        payload = {
            "text": text_chunk,
            "user_id": metadata.get("user_id"),
            "document_id": metadata.get("document_id"), 
            "filename": metadata.get("filename"),
            "chunk_index": metadata.get("chunk_index", 0),
            "created_at": metadata.get("created_at")
        }
        
        # Create point
        point = PointStruct(
            id=point_id,
            vector=embeddings,
            payload=payload
        )
        
        # Upload point
        qdrant_db.client.upsert(
            collection_name=qdrant_db.collection_name,
            points=[point]
        )
        
        return point_id
        
    except Exception as e:
        print(f"Error storing embeddings: {e}")
        raise

def search_similar_chunks(
    query_embedding: List[float],
    user_id: str,
    limit: int = 5,
    score_threshold: float = 0.7
) -> List[Dict[str, Any]]:
    """Search for similar text chunks for a specific user"""
    try:
        # Ensure collection exists before searching
        ensure_collection_exists()
        
        # Filter by user_id to ensure data isolation
        user_filter = Filter(
            must=[
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=user_id)
                )
            ]
        )
        
        # Search
        search_result = qdrant_db.client.search(
            collection_name=qdrant_db.collection_name,
            query_vector=query_embedding,
            query_filter=user_filter,
            limit=limit,
            score_threshold=score_threshold
        )
        
        # Format results
        results = []
        for hit in search_result:
            results.append({
                "text": hit.payload["text"],
                "score": hit.score,
                "metadata": {
                    "document_id": hit.payload.get("document_id"),
                    "filename": hit.payload.get("filename"),
                    "chunk_index": hit.payload.get("chunk_index")
                }
            })
            
        return results
        
    except Exception as e:
        print(f"Error searching similar chunks: {e}")
        raise

def delete_user_documents(user_id: str) -> bool:
    """Delete all documents for a specific user"""
    try:
        # Filter by user_id
        user_filter = Filter(
            must=[
                FieldCondition(
                    key="user_id", 
                    match=MatchValue(value=user_id)
                )
            ]
        )
        
        # Delete points
        qdrant_db.client.delete(
            collection_name=qdrant_db.collection_name,
            points_selector=models.FilterSelector(filter=user_filter)
        )
        
        return True
        
    except Exception as e:
        print(f"Error deleting user documents: {e}")
        return False
