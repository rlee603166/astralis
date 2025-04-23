# src/search/services/embedding_engine.py

from sentence_transformers import SentenceTransformer

_embedding_engine = None

def get_embedding_engine() -> SentenceTransformer:
    global _embedding_engine

    if _embedding_engine is None:
        _embedding_engine = SentenceTransformer(
            "all-MiniLM-L6-v2",
            prompts={
                "classification": "Classify the following text: ",
                "retrieval": "Retrieve semantically similar text: ",
                "clustering": "Identify the topic or theme based on the text: ",
            },
            # backend="onnx"
        )
    return _embedding_engine
