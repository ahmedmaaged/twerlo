from fastapi import UploadFile, HTTPException, status
from typing import List, Dict, Any
from datetime import datetime
import uuid

from app.database.mongodb import get_database
from app.schemas.document import DocumentInDB, DocumentResponse
from app.utils.file_parser import file_parser, text_chunker
from app.services.embedding_service import embedding_service
from app.database.qdrant_client import store_embeddings
from app.config import settings

class DocumentProcessor:
    
    async def process_and_store_document(
        self, 
        file: UploadFile, 
        user_id: str
    ) -> DocumentResponse:
        """Process uploaded document and store embeddings"""
        
        # Validate file
        await self._validate_file(file)
        
        try:
            # Extract text from file
            original_text = await file_parser.extract_text_from_file(file)
            
            if not original_text.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No text content found in the uploaded file"
                )
            
            # Chunk the text
            chunks = text_chunker.chunk_text(original_text)
            
            if not chunks:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to create text chunks from the document"
                )
            
            # Create document record
            document_id = str(uuid.uuid4())
            document_data = {
                "_id": document_id,
                "user_id": user_id,
                "filename": file.filename,
                "content_type": file.content_type,
                "file_size": file.size if file.size else len(original_text),
                "original_text": original_text,
                "chunks_count": len(chunks),
                "created_at": datetime.utcnow()
            }
            
            # Store document in MongoDB
            db = await get_database()
            await db.documents.insert_one(document_data)
            
            # Generate and store embeddings for each chunk
            await self._store_document_embeddings(
                chunks=chunks,
                document_id=document_id,
                user_id=user_id,
                filename=file.filename
            )
            
            # Return document response
            return DocumentResponse(
                id=document_id,
                filename=file.filename,
                content_type=file.content_type,
                file_size=document_data["file_size"],
                chunks_count=len(chunks),
                created_at=document_data["created_at"]
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process document: {str(e)}"
            )
    
    async def _validate_file(self, file: UploadFile):
        """Validate uploaded file"""
        
        # Check file size
        if file.size and file.size > settings.max_file_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds {settings.max_file_size_mb}MB limit"
            )
        
        # Check file type
        allowed_types = ["text/plain", "application/pdf"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type. Allowed types: {', '.join(allowed_types)}"
            )
        
        # Check filename
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required"
            )
    
    async def _store_document_embeddings(
        self,
        chunks: List[Dict[str, Any]],
        document_id: str,
        user_id: str,
        filename: str
    ):
        """Generate embeddings and store in vector database"""
        
        for chunk in chunks:
            try:
                # Generate embedding for chunk text
                embedding = await embedding_service.generate_embedding(chunk["text"])
                
                # Prepare metadata
                metadata = {
                    "user_id": user_id,
                    "document_id": document_id,
                    "filename": filename,
                    "chunk_index": chunk["chunk_index"],
                    "created_at": datetime.utcnow().isoformat()
                }
                
                # Store in Qdrant
                store_embeddings(
                    embeddings=embedding,
                    text_chunk=chunk["text"],
                    metadata=metadata
                )
                
            except Exception as e:
                print(f"Error storing embedding for chunk {chunk['chunk_index']}: {e}")
                # Continue with other chunks even if one fails
                continue
    
    async def get_user_documents(self, user_id: str) -> List[DocumentResponse]:
        """Get all documents for a user"""
        
        db = await get_database()
        cursor = db.documents.find(
            {"user_id": user_id},
            sort=[("created_at", -1)]
        )
        
        documents = []
        async for doc in cursor:
            documents.append(DocumentResponse(
                id=str(doc["_id"]),
                filename=doc["filename"],
                content_type=doc["content_type"],
                file_size=doc["file_size"],
                chunks_count=doc["chunks_count"],
                created_at=doc["created_at"]
            ))
        
        return documents
    
    async def delete_document(self, document_id: str, user_id: str) -> bool:
        """Delete a document and its embeddings"""
        
        try:
            db = await get_database()
            
            # Check if document exists and belongs to user
            document = await db.documents.find_one({
                "_id": document_id,
                "user_id": user_id
            })
            
            if not document:
                return False
            
            # Delete from MongoDB
            await db.documents.delete_one({"_id": document_id})
            
            # TODO: Delete from Qdrant (we'll implement this when we add the delete functionality)
            # For now, we'll leave the embeddings - they're filtered by user_id anyway
            
            return True
            
        except Exception as e:
            print(f"Error deleting document: {e}")
            return False

# Singleton instance
document_processor = DocumentProcessor()
