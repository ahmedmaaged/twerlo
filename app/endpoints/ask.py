from fastapi import APIRouter, Depends, HTTPException, status
import time

from app.schemas.query import QuestionRequest, AnswerResponse, RetrievedChunk
from app.schemas.user import UserInDB
from app.services.auth import get_current_active_user
from app.services.embedding_service import embedding_service
from app.services.llm_service import llm_service
from app.services.logging_service import logging_service
from app.database.qdrant_client import search_similar_chunks

router = APIRouter()

@router.post("/ask", response_model=AnswerResponse)
async def ask_question(
    question_request: QuestionRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Ask a question and get an AI-generated answer based on uploaded documents
    
    - **question**: The question to ask (1-1000 characters)
    - Returns: AI-generated answer with context and metadata
    """
    
    start_time = time.time()
    
    try:
        # Generate embedding for the question
        question_embedding = await embedding_service.generate_embedding(
            question_request.question
        )
        
        # Search for similar chunks in user's documents
        similar_chunks = search_similar_chunks(
            query_embedding=question_embedding,
            user_id=str(current_user.id),
            limit=5,  
            score_threshold=0.1  # lower threshold for text-embedding-3-small model
        )
        
        print(f"DEBUG: User {current_user.id} asked: '{question_request.question}'")
        print(f"DEBUG: Found {len(similar_chunks)} chunks with scores: {[chunk.get('score', 0) for chunk in similar_chunks]}")
        
        # Generate answer using LLM
        answer = await llm_service.generate_answer(
            question=question_request.question,
            context_chunks=similar_chunks
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
        
        # Calculate response time
        end_time = time.time()
        response_time_ms = int((end_time - start_time) * 1000)
        
        # Log the query 
        try:
            await logging_service.log_query(
                user_id=str(current_user.id),
                question=question_request.question,
                answer=answer,
                response_time_ms=response_time_ms,
                retrieved_chunks_count=len(retrieved_chunks)
            )
        except Exception as log_error:
            print(f"Error logging query: {log_error}")
            # Continue without raising error
        
        # Return response
        return AnswerResponse(
            question=question_request.question,
            answer=answer,
            retrieved_chunks=retrieved_chunks,
            response_time_ms=response_time_ms
        )
        
    except Exception as e:
        print(f"Error processing question: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process question and generate answer"
        )
