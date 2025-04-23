# src/search/services/rag_service.py

from typing import Dict, Any
from sentence_transformers import SentenceTransformer
from search.services.pinecone_manager import PineconeManager

class RAGService:
    def __init__(
        self,
        pinecone_manager: PineconeManager,
        embedding_engine: SentenceTransformer
    ):
        self.pinecone_manager = pinecone_manager
        self.embedding_engine = embedding_engine
        
    def query_vector(
        self,
        query: str, 
        namespace: str = "experience", 
        top_k: int = 3
    ) -> dict:
        print("fetching vector db")
        print(f"query: {query}")
        print(f"namespace: {namespace}")
        print(f"top_k: {top_k}")
        embedded_query = self.embedding_engine.encode(query, prompt_name="retrieval")
        
        if hasattr(embedded_query, "tolist"):
            embedded_query = embedded_query.tolist()

        index = self.pinecone_manager._get_index()
        response = index.query(
            namespace=namespace,
            vector=embedded_query,
            top_k=top_k,
            include_metadata=True,
            include_values=False
        )

        return response
