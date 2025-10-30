"""
Enhanced PDF Ingestion Pipeline with Prisma database storage
"""
import os
import json
import PyPDF2
import pdfplumber
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from datetime import datetime
from prisma import Prisma
import asyncio

DATA_DIR = "data"
PDF_DIR = os.path.join(DATA_DIR, "pdfs")
INDEX_DIR = os.path.join(DATA_DIR, "index")
FAISS_INDEX_FILE = os.path.join(INDEX_DIR, "faiss.index")

# Initialize embedding model
print("Loading embedding model...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize Prisma client
db = Prisma()

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using pdfplumber (better for structured text)"""
    text_by_page = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    text_by_page.append({
                        "page": i + 1,
                        "text": text.strip()
                    })
    except Exception as e:
        print(f"Error with pdfplumber, trying PyPDF2: {e}")
        # Fallback to PyPDF2
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for i, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    if text:
                        text_by_page.append({
                            "page": i + 1,
                            "text": text.strip()
                        })
        except Exception as e2:
            print(f"Error extracting PDF {pdf_path}: {e2}")

    return text_by_page

def chunk_text(text, chunk_size=500, overlap=100):
    """Split text into overlapping chunks"""
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if len(chunk.strip()) > 50:  # Only keep meaningful chunks
            chunks.append(chunk.strip())

    return chunks

def clean_text(text):
    """Clean and normalize text"""
    text = ' '.join(text.split())
    text = text.replace('\n', ' ').replace('\t', ' ')
    return text

async def process_pdfs_to_db():
    """Process all PDFs and store in database"""
    if not os.path.exists(PDF_DIR):
        print(f"Error: {PDF_DIR} directory not found!")
        return []

    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')]

    if not pdf_files:
        print(f"No PDF files found in {PDF_DIR}")
        return []

    await db.connect()
    all_chunks = []

    for pdf_file in pdf_files:
        print(f"\nProcessing: {pdf_file}")
        pdf_path = os.path.join(PDF_DIR, pdf_file)
        file_size = os.path.getsize(pdf_path)

        # Extract text
        pages = extract_text_from_pdf(pdf_path)
        print(f"  Extracted {len(pages)} pages")

        # Create or update document record
        document = await db.document.upsert(
            where={"filename": pdf_file},
            data={
                "create": {
                    "filename": pdf_file,
                    "title": pdf_file.replace('.pdf', '').replace('_', ' '),
                    "fileSize": file_size,
                    "pageCount": len(pages)
                },
                "update": {
                    "fileSize": file_size,
                    "pageCount": len(pages)
                }
            }
        )

        # Delete old chunks for this document
        await db.docchunk.delete_many(where={"documentId": document.id})

        chunk_id = 0
        # Process each page
        for page_data in pages:
            page_num = page_data['page']
            text = clean_text(page_data['text'])

            # Create chunks
            chunks = chunk_text(text)

            for chunk in chunks:
                # Save to database
                db_chunk = await db.docchunk.create(
                    data={
                        "documentId": document.id,
                        "pageNumber": page_num,
                        "chunkText": chunk,
                        "vectorId": chunk_id
                    }
                )

                all_chunks.append({
                    "id": chunk_id,
                    "db_id": db_chunk.id,
                    "document": pdf_file,
                    "page": page_num,
                    "text": chunk
                })
                chunk_id += 1

        print(f"  Created {chunk_id} chunks for {pdf_file}")

    return all_chunks

def create_embeddings(chunks):
    """Create embeddings for all chunks"""
    if not chunks:
        print("No chunks to embed!")
        return None

    print(f"\nGenerating embeddings for {len(chunks)} chunks...")
    texts = [chunk['text'] for chunk in chunks]
    embeddings = embedding_model.encode(texts, show_progress_bar=True, batch_size=32)

    return embeddings

def create_faiss_index(embeddings):
    """Create FAISS index for fast similarity search"""
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings.astype('float32'))
    print(f"FAISS index created with {index.ntotal} vectors")
    return index

def save_faiss_index(index):
    """Save FAISS index to disk"""
    os.makedirs(INDEX_DIR, exist_ok=True)
    faiss.write_index(index, FAISS_INDEX_FILE)
    print(f"\nFAISS index saved: {FAISS_INDEX_FILE}")

async def main():
    """Main ingestion pipeline"""
    print("=" * 60)
    print("LegalBot - PDF Ingestion Pipeline (Prisma + FAISS)")
    print("=" * 60)

    # Step 1: Process PDFs and store in database
    chunks = await process_pdfs_to_db()

    if not chunks:
        print("\n⚠️  No chunks created. Please add PDF files to data/pdfs/")
        await db.disconnect()
        return

    print(f"\n✓ Total chunks created: {len(chunks)}")

    # Step 2: Create embeddings
    embeddings = create_embeddings(chunks)

    if embeddings is None:
        await db.disconnect()
        return

    print(f"✓ Embeddings shape: {embeddings.shape}")

    # Step 3: Create FAISS index
    index = create_faiss_index(embeddings)

    # Step 4: Save FAISS index
    save_faiss_index(index)

    await db.disconnect()

    print("\n" + "=" * 60)
    print("✓ Ingestion complete! Database and index are ready.")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())

