# src/search/services/pinecone_manager.py

from search.config import pincone_config, embedding_config
from typing import Any, Dict, List, Optional, Tuple
from pinecone import Index, Pinecone, PineconeException

class PineconeManager():
    def __init__(self):
        self.api_key = pincone_config.API_KEY
        self.index_name = pincone_config.INDEX_NAME
        self.dimension = embedding_config.DIMENSION
        self.metric = pincone_config.METRIC
        self.cloud = pincone_config.CLOUD
        self.region = pincone_config.REGION
        self.client: Optional[Pinecone] = None
        self.index: Optional[Index] = None

        self._init_client()

    def _init_client(self):
        self.client = Pinecone(api_key=self.api_key)

    def _get_index(self) -> Index:
        if self.client is None:
            self._init_client()

        self.index = self.client.Index(self.index_name)
        return self.index
 
    def upsert_vector(
        self,
        vector_id: str,
        vector: List[float],
        metadata: Dict[str, Any]
    ) -> bool:
        try:
            index = self._get_index()

            response = index.upsert(vectors=[(vector_id, vector, metadata)])
            return response.upserted_count == 1
        except PineconeException as e:
            print(f"PineconeException during batch upsert: {e}")
            return False

    def upsert_batch(self, vectors: List[Tuple[str, List[float], Dict[str, Any]]]) -> bool:
        try:
            index = self._get_index()

            for vec_id, vec_values, _ in vectors:
                if len(vec_values) != self.dimension:
                    print(f"vector ({vec_id}) is not the correct size: {len(vec_values)}")
                    return False

            chunk_size = 100
            total_upserted = 0
            for i in range(0, len(vectors), chunk_size):
                chunk = vectors[i:i + chunk_size]
                upsert_response = index.upsert(vectors=chunk)
                total_upserted += upsert_response.upserted_count

            return True
        except PineconeException as e:
            print(f"PineconeException during batch upsert: {e}")
            return False

