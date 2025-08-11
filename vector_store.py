import os
import logging
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings

logger = logging.getLogger(__name__)

embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    dimensions=1536
)

VECTOR_DIR = "jim_vectorstore"

def create_vector_store_from_texts(texts):
    logger.info("🆕 Creating new vector store with texts: %s", texts)
    db = FAISS.from_texts(texts, embedding=embedding_model)
    db.save_local(VECTOR_DIR)
    return db

def load_vector_store():
    logger.info("📂 Loading vector store from: %s", VECTOR_DIR)
    return FAISS.load_local(VECTOR_DIR, embedding_model)

def search_similar_texts(query, k=3):
    logger.info("🔍 Searching vector store for: '%s' (top %d)", query, k)
    db = load_vector_store()
    results = db.similarity_search(query, k=k)
    logger.info("✅ Vector search results: %s", [doc.page_content for doc in results])
    return [doc.page_content for doc in results]

def add_text_to_vector_store(texts):
    try:
        logger.info("➕ Adding texts to vector store: %s", texts)
        db = load_vector_store()
        db.add_texts(texts)
        db.save_local(VECTOR_DIR)
        logger.info("✅ Vector store updated and saved.")
    except Exception as e:
        logger.warning("⚠️ Failed to load vector store, creating new one. Error: %s", e)
        create_vector_store_from_texts(texts)
