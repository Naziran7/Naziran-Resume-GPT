import logging
import numpy as np
from typing import List

logger = logging.getLogger(__name__)

# Lazy loaded SentenceTransformer model singleton
_model_instance = None

def get_embedding_model():
    global _model_instance
    if _model_instance is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Initializing SentenceTransformer 'all-MiniLM-L6-v2' (384 dimensions)...")
            _model_instance = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("SentenceTransformer model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load sentence-transformers library: {str(e)}. Running in vector mock mode.")
            _model_instance = "mock"
    return _model_instance

class EmbeddingService:
    def __init__(self):
        # Trigger lazy load validation
        get_embedding_model()

    def chunk_text(self, text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
        """Split text into overlapping character chunks of standard sizes."""
        if not text:
            return []
        
        # Clean double line breaks
        text = " ".join(text.split())
        
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            # Shift window
            end = start + chunk_size
            if end >= text_len:
                chunks.append(text[start:])
                break
                
            # Try to slide window back slightly to split on word boundary
            boundary = text.rfind(" ", start, end)
            if boundary > start + (chunk_size // 2):
                end = boundary
                
            chunks.append(text[start:end].strip())
            start = end - chunk_overlap
            
            # Prevent infinite loops on long strings without spaces
            if start >= end:
                start = end + 1
                
        return [c for c in chunks if len(c) > 10]

    def generate_embedding(self, text: str) -> List[float]:
        """Convert a text chunk into a 384-dimensional floating point vector."""
        model = get_embedding_model()
        
        if model == "mock":
            # Generate a deterministic normalized mock vector based on the hash of the text
            text_hash = hash(text)
            rng = np.random.default_rng(abs(text_hash) % (2**32))
            vector = rng.standard_normal(384)
            # Normalize vector to unit length
            norm = np.linalg.norm(vector)
            normalized = (vector / norm).tolist() if norm > 0 else [0.0] * 384
            return normalized
            
        try:
            # sentence-transformers outputs numpy array, convert to standard Python float list
            embedding = model.encode(text, convert_to_numpy=True)
            # Normalize to unit length (cosine similarity becomes equivalent to dot product)
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error encoding embedding via SentenceTransformer: {str(e)}")
            # Failover to mock vector
            text_hash = hash(text)
            rng = np.random.default_rng(abs(text_hash) % (2**32))
            vector = rng.standard_normal(384)
            norm = np.linalg.norm(vector)
            return (vector / norm).tolist() if norm > 0 else [0.0] * 384
