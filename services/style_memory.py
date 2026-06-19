import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path
import uuid

DB_PATH = str(Path(__file__).parent.parent / "chroma_db")

def _get_collection(user_id: int, content_type: str):
    client = chromadb.PersistentClient(path=DB_PATH)
    ef = embedding_functions.DefaultEmbeddingFunction()
    name = f"style_u{user_id}_{content_type}"
    return client.get_or_create_collection(name=name, embedding_function=ef)

def store_approved_post(user_id: int, content_type: str, text: str, news_title: str, conviction_score: float = 0.5):
    """Store an approved post so future content can match its style."""
    try:
        col = _get_collection(user_id, content_type)
        col.add(
            documents=[text],
            metadatas=[{"news_title": news_title, "conviction_score": conviction_score}],
            ids=[str(uuid.uuid4())]
        )
        print(f"   📚 Style memory updated ({content_type}: {col.count()} examples stored)")
    except Exception as e:
        print(f"   ⚠️ Style memory store error: {e}")

def get_style_examples(user_id: int, content_type: str, query: str, n: int = 2) -> list:
    """Retrieve the most stylistically similar past approved posts."""
    try:
        col = _get_collection(user_id, content_type)
        count = col.count()
        if count == 0:
            return []
        results = col.query(query_texts=[query], n_results=min(n, count))
        return results["documents"][0] if results["documents"] else []
    except Exception as e:
        print(f"   ⚠️ Style memory retrieve error: {e}")
        return []
