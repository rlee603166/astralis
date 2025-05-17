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


class NeoConfig:
    """Configuration for Neo4j"""
    NEO4J_URI: str = settings.NEO4J_URI
    NEO4J_USERNAME: str = settings.NEO4J_USERNAME
    NEO4J_PASSWORD: str = settings.NEO4J_PASSWORD
    AURA_INSTANCEID: str = settings.AURA_INSTANCEID
    AURA_INSTANCENAME: str = settings.AURA_INSTANCENAME


embedding_config    = EmbeddingConfig()
pincone_config      = PineconeConfig()
neo_config          = NeoConfig()
