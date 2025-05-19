# src/search/services/rag_service.py

from typing import Dict, Any
from sentence_transformers import SentenceTransformer
from search.services.pinecone_manager import PineconeManager
from search.services.neo_manager import NeoManager

class RAGService:
    def __init__(
        self,
        neo_manager: NeoManager,
        pinecone_manager: PineconeManager,
        embedding_engine: SentenceTransformer
    ):
        self.neo_manager        = neo_manager
        self.pinecone_manager   = pinecone_manager
        self.embedding_engine   = embedding_engine
        
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

    async def query_graph(self, cypher_query: str):
        print("[FETCH]: Querying knowledge graph")
        print(f"[CYPHER]: \n{cypher_query}")
        try:
            async with self.neo_manager._get_driver() as driver:
                records, _, _ = await driver.execute_query(cypher_query, database_="neo4j")
            return records
        except Exception as e:
            return f"Error running Cypher: {str(e)}"
