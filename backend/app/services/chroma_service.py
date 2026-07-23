import time
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any

class ChromaMemoryLayer:
    def __init__(self, persist_path="./chroma_data"):
        # Setup persistent offline ChromaDB storage
        self.client = chromadb.PersistentClient(path=persist_path)
        
        # Setup native local embedding function (SentenceTransformers all-MiniLM-L6-v2)
        # Bypasses network requests & OpenAI API keys, utilizing CPU compute locally (384 dimensions)
        self.emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Get or create contextual memory collection using cosine distance metric
        self.collection = self.client.get_or_create_collection(
            name="client_contextual_memory",
            embedding_function=self.emb_fn,
            metadata={"hnsw:space": "cosine"}
        )

    async def retrieve_client_facts(self, client_id: str, query: str) -> List[str]:
        """Queries local vector space with strict client_id metadata filtering (multi-tenant boundary)."""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=2,
                where={"client_id": client_id}  # The security guardrail
            )
            if not results or not results.get('documents') or not results['documents'][0]:
                return []
            return results['documents'][0]
        except Exception:
            return []

    async def add_client_fact(self, client_id: str, fact_id: str, fact_text: str, domain: str) -> str:
        """Stores approved declarative preferences in multi-tenant collection."""
        try:
            self.collection.add(
                ids=[fact_id],
                documents=[fact_text],
                metadatas=[{
                    "client_id": client_id,
                    "domain": domain,
                    "timestamp": int(time.time())
                }]
            )
            return fact_id
        except Exception as e:
            raise RuntimeError(f"ChromaDB insert failure: {str(e)}")
