import openai
from typing import List, Dict, Any
from app.config import settings

class LLMService:
    
    def __init__(self):
        # Configure OpenAI-compatible client with separate LLM API key
        self.client = openai.OpenAI(
            api_key=settings.llm_api_key,  # Separate API key for LLM provider
            base_url=settings.llm_base_url  # Dynamic base URL for any OpenAI-compatible API
        )
        
        # Dynamic model configuration from environment
        self.model = settings.llm_model_name
        self.max_tokens = settings.llm_max_tokens
        self.temperature = settings.llm_temperature
        
        print(f"LLM Service initialized with provider: {settings.llm_base_url}")
        print(f"Using model: {self.model}")
    
    async def generate_answer(
        self, 
        question: str, 
        context_chunks: List[Dict[str, Any]]
    ) -> str:
        """
        Generate answer based on question and retrieved context chunks
        
        Args:
            question: User's question
            context_chunks: List of relevant text chunks with metadata
            
        Returns:
            Generated answer string
        """
        
        try:
            # Prepare context from chunks
            context_text = self._prepare_context(context_chunks)
            
            # Create system prompt
            system_prompt = self._get_system_prompt()
            
            # Create user prompt with context and question
            user_prompt = self._create_user_prompt(question, context_text)
            
            # Generate response using OpenAI-compatible API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=False
            )
            
            # Extract answer
            answer = response.choices[0].message.content.strip()
            
            return answer
            
        except Exception as e:
            print(f"Error generating answer: {e}")
            raise ValueError(f"Failed to generate answer: {str(e)}")
    
    def _prepare_context(self, context_chunks: List[Dict[str, Any]]) -> str:
        """Prepare context text from retrieved chunks"""
        
        if not context_chunks:
            return "No relevant context found."
        
        context_parts = []
        for i, chunk in enumerate(context_chunks, 1):
            text = chunk.get("text", "")
            filename = chunk.get("metadata", {}).get("filename", "Unknown")
            
            context_parts.append(f"[Context {i} from {filename}]:\n{text}")
        
        return "\n\n".join(context_parts)
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for the LLM"""
        
        return """You are a friendly helpful multilingual AI assistant that answers questions based on provided context documents. 

INSTRUCTIONS:
1. Answer the user's question using ONLY the information provided in the context
2. If the context doesn't contain enough information to answer the question, say so clearly
3. Be concise but comprehensive in your response
4. If you reference specific information, you can mention which document it came from
5. Do not make up information that isn't in the provided context
6. If the question is unclear, ask for clarification

RESPONSE FORMAT:
- Provide a direct answer to the question
- Keep responses focused and relevant
- Use clear, professional but friendly language"""
    
    def _create_user_prompt(self, question: str, context: str) -> str:
        """Create user prompt with question and context"""
        
        return f"""CONTEXT DOCUMENTS:
{context}

QUESTION:
{question}

Please answer the question based on the provided context documents. If the context doesn't contain sufficient information to answer the question, please state that clearly."""

# Singleton instance
llm_service = LLMService()
