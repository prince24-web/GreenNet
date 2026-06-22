import os
import chromadb
from chromadb.config import Settings
from .llm import embed

CHROMA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'chroma_db')
COLLECTION_NAME = "agrisense_knowledge"


def get_chroma_client():
    """Get a persistent ChromaDB client that saves to disk."""
    client = chromadb.PersistentClient(
        path=CHROMA_PATH,
        settings=Settings(anonymized_telemetry=False)
    )
    return client


def get_collection():
    """Get or create the knowledge collection."""
    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}  # cosine similarity — best for text
    )
    return collection


def add_document(doc_id: str, text: str, metadata: dict = {}):
    """
    Add a single document to ChromaDB.
    Embeds it using nomic-embed-text via Ollama, then stores it.
    """
    collection = get_collection()

    # Check if document already exists — avoid duplicates on re-run
    existing = collection.get(ids=[doc_id])
    if existing['ids']:
        return  # already indexed

    vector = embed(text)
    if not vector:
        print(f"  ✗ Failed to embed: {doc_id}")
        return

    collection.add(
        ids=[doc_id],
        embeddings=[vector],
        documents=[text],
        metadatas=[metadata]
    )


def search(query: str, n_results: int = 3) -> list[dict]:
    """
    Search the knowledge base for documents relevant to a query.
    Returns list of {text, metadata, distance} dicts.
    """
    collection = get_collection()

    # Check collection isn't empty
    count = collection.count()
    if count == 0:
        return []

    vector = embed(query)
    if not vector:
        return []

    results = collection.query(
        query_embeddings=[vector],
        n_results=min(n_results, count),
        include=["documents", "metadatas", "distances"]
    )

    output = []
    for i in range(len(results['ids'][0])):
        output.append({
            "text": results['documents'][0][i],
            "metadata": results['metadatas'][0][i],
            "distance": results['distances'][0][i]
        })

    return output


def retrieve_context(query: str, n_results: int = 3) -> str:
    """
    Master retrieval function — called by the orchestrator.
    Returns a formatted string ready to inject into an LLM prompt.
    """
    results = search(query, n_results=n_results)

    if not results:
        return ""

    lines = ["RETRIEVED KNOWLEDGE:"]
    for i, r in enumerate(results, 1):
        # Only include results that are actually relevant (distance < 0.7)
        if r['distance'] < 0.7:
            source = r['metadata'].get('source', 'AgriSense KB')
            category = r['metadata'].get('category', '')
            lines.append(f"\n[{i}] Source: {source} | Category: {category}")
            lines.append(r['text'])

    if len(lines) == 1:  # only the header, nothing passed threshold
        return ""

    return "\n".join(lines)


def get_collection_stats() -> dict:
    """How many documents are in the knowledge base."""
    collection = get_collection()
    return {"total_documents": collection.count()}