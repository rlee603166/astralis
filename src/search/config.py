# src/search/config.py

from config import settings

class EmbeddingConfig:
    """Configuration for embedding generation."""
    MODEL_NAME: str = settings.EMBEDDING_MODEL  # Use settings value
    DIMENSION: int = settings.EMBEDDING_DIMENSION  # Use settings value
    MAX_TOKENS_PER_CHUNK: int = 8000  # Static value, adjustable as needed

class PineconeConfig:
    """Configuration for Pinecone vector database."""
    API_KEY: str = settings.PINECONE_API_KEY
    INDEX_NAME: str = settings.PINECONE_INDEX_NAME
    METRIC: str = "cosine"  # Static default, can be made configurable if needed
    CLOUD: str = settings.PINECONE_CLOUD
    REGION: str = settings.PINECONE_REGION




embedding_config = EmbeddingConfig()
pincone_config = PineconeConfig()
