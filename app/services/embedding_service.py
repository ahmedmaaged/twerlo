import openai
from typing import List
from app.config import settings

class EmbeddingService:
    
    def __init__(self):
        # Configure OpenAI-compatible client with separate embedding API key
        self.client = openai.OpenAI(
            api_key=settings.embedding_api_key,  # Separate API key for embedding provider
            base_url=settings.embedding_base_url  # Dynamic base URL for any OpenAI-compatible API
        )
        
        # Dynamic model configuration from environment
        self.model = settings.embedding_model_name
        self.dimensions = settings.embedding_dimensions
        
        print(f"Embedding Service initialized with provider: {settings.embedding_base_url}")
        print(f"Using model: {self.model} (dimensions: {self.dimensions})")
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for given text"""
        
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        try:
            # Create embedding using OpenAI-compatible API
            response = self.client.embeddings.create(
                model=self.model,
                input=text.strip()
            )
            
            # Extract embedding vector
            embedding = response.data[0].embedding
            
            return embedding
            
        except Exception as e:
            print(f"Error generating embedding: {e}")
            raise ValueError(f"Failed to generate embedding: {str(e)}")
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts in batch"""
        
        if not texts:
            return []
        
        # Filter out empty texts
        valid_texts = [text.strip() for text in texts if text and text.strip()]
        
        if not valid_texts:
            raise ValueError("No valid texts provided")
        
        try:
            # Create embeddings in batch using OpenAI-compatible API
            response = self.client.embeddings.create(
                model=self.model,
                input=valid_texts
            )
            
            # Extract embedding vectors
            embeddings = [data.embedding for data in response.data]
            
            return embeddings
            
        except Exception as e:
            print(f"Error generating batch embeddings: {e}")
            raise ValueError(f"Failed to generate batch embeddings: {str(e)}")

# Singleton instance
embedding_service = EmbeddingService()
