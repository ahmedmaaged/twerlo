import PyPDF2
from typing import List, Dict, Any
import io
from fastapi import UploadFile

class FileParser:
    
    @staticmethod
    async def extract_text_from_file(file: UploadFile) -> str:
        """Extract text from uploaded file"""
        
        if file.content_type == "text/plain":
            return await FileParser._extract_from_txt(file)
        elif file.content_type == "application/pdf":
            return await FileParser._extract_from_pdf(file)
        else:
            raise ValueError(f"Unsupported file type: {file.content_type}")
    
    @staticmethod
    async def _extract_from_txt(file: UploadFile) -> str:
        """Extract text from TXT file"""
        content = await file.read()
        try:
            # Try UTF-8 first
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            # Fallback to latin-1
            text = content.decode('latin-1')
        
        return text.strip()
    
    @staticmethod
    async def _extract_from_pdf(file: UploadFile) -> str:
        """Extract text from PDF file"""
        content = await file.read()
        pdf_file = io.BytesIO(content)
        
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
            
            return text.strip()
        
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")

class TextChunker:
    
    @staticmethod
    def chunk_text(
        text: str, 
        chunk_size: int = 1000, 
        overlap: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Input text to chunk
            chunk_size: Maximum size of each chunk
            overlap: Number of characters to overlap between chunks
        
        Returns:
            List of chunk dictionaries with text, start_char, end_char, chunk_index
        """
        if not text or len(text) == 0:
            return []
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            # Calculate end position
            end = start + chunk_size
            
            # If this isn't the last chunk, try to break at a sentence or word boundary
            if end < len(text):
                # Look for sentence boundaries (. ! ?) within the last 100 characters
                sentence_end = -1
                for i in range(min(100, end - start)):
                    pos = end - i - 1
                    if pos > start and text[pos] in '.!?':
                        # Check if next character is space or end of text
                        if pos + 1 >= len(text) or text[pos + 1].isspace():
                            sentence_end = pos + 1
                            break
                
                if sentence_end > 0:
                    end = sentence_end
                else:
                    # Look for word boundaries (spaces) within the last 50 characters
                    word_end = -1
                    for i in range(min(50, end - start)):
                        pos = end - i - 1
                        if pos > start and text[pos].isspace():
                            word_end = pos
                            break
                    
                    if word_end > 0:
                        end = word_end
            
            # Extract chunk text
            chunk_text = text[start:end].strip()
            
            if chunk_text:  # Only add non-empty chunks
                chunks.append({
                    "text": chunk_text,
                    "start_char": start,
                    "end_char": end,
                    "chunk_index": chunk_index
                })
                chunk_index += 1
            
            # Move start position for next chunk (with overlap)
            start = max(start + 1, end - overlap)
            
            # Prevent infinite loop
            if start >= len(text):
                break
        
        return chunks

# Singleton instances
file_parser = FileParser()
text_chunker = TextChunker()
