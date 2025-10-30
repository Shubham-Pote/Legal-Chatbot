"""
Enhanced Retrieval System with Prisma database integration
"""
import os
import faiss
from sentence_transformers import SentenceTransformer
from prisma import Prisma

INDEX_DIR = "data/index"
FAISS_INDEX_FILE = os.path.join(INDEX_DIR, "faiss.index")

# Load embedding model
embedding_model = None
faiss_index = None
db = Prisma()

async def initialize():
    """Initialize retrieval system - load index, model, and connect to DB"""
    global embedding_model, faiss_index

    if embedding_model is None:
        print("Loading embedding model...")
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    if faiss_index is None:
        if os.path.exists(FAISS_INDEX_FILE):
            print("Loading FAISS index...")
            faiss_index = faiss.read_index(FAISS_INDEX_FILE)
        else:
            raise FileNotFoundError(f"FAISS index not found. Please run: python backend/ingestion_prisma.py")

    if not db.is_connected():
        await db.connect()

    return True

async def search(query, top_k=5):
    """
    Search for relevant chunks given a query

    Args:
        query: User's legal question
        top_k: Number of top results to return

    Returns:
        List of relevant chunks with scores
    """
    await initialize()

    # Embed the query
    query_embedding = embedding_model.encode([query])

    # Search in FAISS
    distances, indices = faiss_index.search(query_embedding.astype('float32'), top_k)

    # Get chunk details from database
    results = []
    for i, (distance, vector_id) in enumerate(zip(distances[0], indices[0])):
        # Find chunk by vectorId
        chunk = await db.docchunk.find_first(
            where={"vectorId": int(vector_id)},
            include={"document": True}
        )

        if chunk:
            results.append({
                "id": chunk.id,
                "vector_id": vector_id,
                "document": chunk.document.filename,
                "document_title": chunk.document.title,
                "page": chunk.pageNumber,
                "text": chunk.chunkText,
                "score": float(distance),
                "rank": i + 1
            })

    return results

def format_sources(results):
    """Format retrieval results as readable sources"""
    sources = []

    for result in results:
        source = {
            "document": result['document'],
            "page": result['page'],
            "text": result['text'][:200] + "..." if len(result['text']) > 200 else result['text'],
            "score": result['score']
        }
        sources.append(source)

    return sources

def get_context_for_llm(results, max_length=3000):
    """
    Prepare context from retrieval results for LLM

    Args:
        results: List of retrieved chunks
        max_length: Maximum character length for context

    Returns:
        Formatted context string
    """
    context_parts = []
    current_length = 0

    for i, result in enumerate(results):
        source_text = f"[Source {i+1}: {result['document_title'] or result['document']}, Page {result['page']}]\n{result['text']}\n"

        if current_length + len(source_text) <= max_length:
            context_parts.append(source_text)
            current_length += len(source_text)
        else:
            break

    return "\n".join(context_parts)

def check_index_exists():
    """Check if FAISS index exists"""
    return os.path.exists(FAISS_INDEX_FILE)

async def get_index_stats():
    """Get statistics about the indexed documents"""
    try:
        if not db.is_connected():
            await db.connect()

        # Count documents and chunks
        doc_count = await db.document.count()
        chunk_count = await db.docchunk.count()

        # Get document list
        documents = await db.document.find_many()

        return {
            "total_chunks": chunk_count,
            "document_count": doc_count,
            "documents": [
                {
                    "filename": doc.filename,
                    "title": doc.title,
                    "pages": doc.pageCount,
                    "uploaded": doc.uploadedAt.isoformat()
                }
                for doc in documents
            ],
            "index_exists": check_index_exists()
        }
    except Exception as e:
        print(f"Error getting stats: {e}")
        return None

async def cleanup():
    """Disconnect from database"""
    if db.is_connected():
        await db.disconnect()

