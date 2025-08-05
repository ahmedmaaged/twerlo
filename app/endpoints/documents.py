from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status, Path
from typing import List

from app.schemas.document import DocumentResponse
from app.schemas.user import UserInDB
from app.schemas.document import RetrievedChunk, DocumentListResponse, DeleteResponse, TestRetrievalRequest, TestRetrievalResponse

from app.services.auth import get_current_active_user
from app.services.document_processor import document_processor
from app.database.mongodb import get_database
from app.services.embedding_service import embedding_service
from app.database.qdrant_client import search_similar_chunks

router = APIRouter()

@router.get("/", response_model=List[DocumentListResponse])
async def list_user_documents(
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    List all documents uploaded by the current user
    
    - Returns: List of documents with metadata
    """
    
    try:
        db = await get_database()
        documents_collection = db.documents
        
        # Find all documents for the current user
        cursor = documents_collection.find(
            {"user_id": str(current_user.id)},
            {"original_text": 0}  # Exclude large text field
        ).sort("created_at", -1)  # Most recent first
        
        documents = []
        async for doc in cursor:
            documents.append(DocumentListResponse(
                id=str(doc["_id"]),
                filename=doc["filename"],
                content_type=doc["content_type"],
                file_size=doc["file_size"],
                chunks_count=doc["chunks_count"],
                created_at=doc["created_at"].isoformat()
            ))
        
        return documents
        
    except Exception as e:
        print(f"Error listing documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list documents"
        )

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload (PDF or TXT format)"),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Upload and process a document (PDF or TXT)
    
    - **file**: Document file to upload (PDF or TXT format)
    - Returns: Document information including ID and processing details
    """
    
    try:
        document = await document_processor.process_and_store_document(
            file=file,
            user_id=str(current_user.id)
        )
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload and process document"
        )


@router.delete("/{document_id}", response_model=DeleteResponse)
async def delete_document(
    document_id: str = Path(..., description="ID of the document to delete"),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Delete a specific document and its associated chunks
    
    - **document_id**: The ID of the document to delete
    - Returns: Confirmation of deletion
    """
    
    try:
        db = await get_database()
        documents_collection = db.documents
        
        # First, verify the document exists and belongs to the user
        document = await documents_collection.find_one({
            "_id": document_id,
            "user_id": str(current_user.id)
        })
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or access denied"
            )
        
        # Delete from MongoDB
        delete_result = await documents_collection.delete_one({
            "_id": document_id,
            "user_id": str(current_user.id)
        })
        
        if delete_result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Delete associated chunks from Qdrant
        from app.database.qdrant_client import qdrant_db
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        from qdrant_client.http import models
        
        document_filter = Filter(
            must=[
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=str(current_user.id))
                ),
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id)
                )
            ]
        )
        
        qdrant_db.client.delete(
            collection_name=qdrant_db.collection_name,
            points_selector=models.FilterSelector(filter=document_filter)
        )
        
        return DeleteResponse(
            message="Document deleted successfully",
            deleted_document_id=document_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )


@router.post("/query", response_model=TestRetrievalResponse)
async def test_retrieval(
    test_request: TestRetrievalRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Test retrieval system without LLM generation - for debugging
    
    - **query**: The query to test retrieval for
    - Returns: Detailed retrieval information including embeddings and scores
    """
    
    try:
        # Generate embedding for the query
        query_embedding = await embedding_service.generate_embedding(
            test_request.query
        )
        
        # search parameters
        score_threshold = test_request.score_threshold
        limit = test_request.limit 
        
        # Search for similar chunks in user's documents
        similar_chunks = search_similar_chunks(
            query_embedding=query_embedding,
            user_id=str(current_user.id),
            limit=limit,  # Get more results for testing
            score_threshold=score_threshold
        )
        
        # Format retrieved chunks for response
        retrieved_chunks = [
            RetrievedChunk(
                text=chunk["text"],
                score=chunk["score"],
                metadata=chunk["metadata"]
            )
            for chunk in similar_chunks
        ]
        
        # Return test response
        return TestRetrievalResponse(
            query=test_request.query,
            embedding_preview=query_embedding[:5],  # First 5 values
            chunks_found=len(retrieved_chunks),
            retrieved_chunks=retrieved_chunks,
            score_threshold_used=score_threshold
        )
        
    except Exception as e:
        print(f"Error testing retrieval: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test retrieval: {str(e)}"
        )