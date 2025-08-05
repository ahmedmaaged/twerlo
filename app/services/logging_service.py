from datetime import datetime
from app.database.mongodb import get_database

class LoggingService:
    
    async def log_query(
        self,
        user_id: str,
        question: str,
        answer: str,
        response_time_ms: int,
        retrieved_chunks_count: int
    ) -> str:
        """
        Log a query and response to the database
        
        Args:
            user_id: ID of the user who asked the question
            question: The question asked
            answer: The generated answer
            response_time_ms: Time taken to generate response in milliseconds
            retrieved_chunks_count: Number of chunks retrieved for context
            
        Returns:
            ID of the logged query
        """
        
        try:
            # Prepare log data
            log_data = {
                "user_id": user_id,
                "question": question,
                "answer": answer,
                "response_time_ms": response_time_ms,
                "retrieved_chunks_count": retrieved_chunks_count,
                "timestamp": datetime.utcnow()
            }
            
            # Store in MongoDB
            db = await get_database()
            result = await db.query_logs.insert_one(log_data)
            
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"Error logging query: {e}")
            # Don't raise exception for logging failures - just log and continue
            return None
    

# Singleton instance
logging_service = LoggingService()
