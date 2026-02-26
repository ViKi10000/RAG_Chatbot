"""Main FastAPI application for RAG Chatbot."""

import os
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import RAG components with error handling
try:
    from src.data_loader import DataLoader
    from src.embedding import EmbeddingManager
    from src.vectorstore import VectorStore
    from src.search import RAGRetriever
    from src.llm import GroqLLM, RAGPipeline
except ImportError as e:
    logger.error(f"Failed to import RAG components: {e}")
    logger.info("Make sure all dependencies are installed: uv sync")
    raise

# Initialize FastAPI app
app = FastAPI(
    title="RAG Chatbot API",
    description="Domain-specific AI chatbot using Retrieval Augmented Generation",
    version="1.0.0"
)

# Domain Configuration (customize this)
DOMAIN_CONFIG = {
    "domain": os.getenv("DOMAIN", "general"),  
    "domain_specific_prompt": os.getenv("DOMAIN_PROMPT", "You are a helpful AI assistant."),
    "max_context_length": int(os.getenv("MAX_CONTEXT", "3000")),
    "temperature": float(os.getenv("TEMPERATURE", "0.7")),
    "max_tokens": int(os.getenv("MAX_TOKENS", "1024")),
}

# CORS: allow all by default; set CORS_ORIGINS to e.g. "https://app.example.com" to restrict
_cors_origins = os.getenv("CORS_ORIGINS", "*")
allow_origins = [o.strip() for o in _cors_origins.split(",") if o.strip()] if _cors_origins else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for RAG pipeline
rag_pipeline: Optional[RAGPipeline] = None
vector_store: Optional[VectorStore] = None
embedding_manager: Optional[EmbeddingManager] = None
retriever: Optional[RAGRetriever] = None
llm: Optional[GroqLLM] = None
data_loader: Optional[DataLoader] = None

# Lock for thread-safe operations
pipeline_lock = threading.Lock()


# Pydantic models
class QueryRequest(BaseModel):
    """Request model for query endpoint."""
    question: str
    top_k: int = 5
    # Use a low default so we rarely drop all results.
    # Additional safety logic in the retriever will fall back
    # to returning the top results even if this threshold
    # filters everything out.
    min_score: float = 0.0


class QueryResponse(BaseModel):
    """Response model for query endpoint."""
    question: str
    answer: str
    document_count: int
    confidence: float
    sources: Optional[List[Dict[str, Any]]] = None


class DataLoadRequest(BaseModel):
    """Request model for loading documents."""
    data_directory: str


def _default_embedding_model() -> str:
    return os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")


def _default_llm_model() -> str:
    return os.getenv("GROQ_LLM_MODEL", "llama-3.1-8b-instant")


class InitializeRequest(BaseModel):
    """Request model for pipeline initialization."""
    model_name: Optional[str] = None  # set from env in endpoint if not provided
    llm_model: Optional[str] = None  # set from env in endpoint if not provided


# Initialization functions
def initialize_pipeline(
    model_name: str = None,
    llm_model: str = None,
    force: bool = False,
):
    """Initialize the RAG pipeline."""
    global rag_pipeline, vector_store, embedding_manager, retriever, llm, data_loader

    with pipeline_lock:
        try:
            # Avoid re-initializing everything if we already
            # have a working pipeline, unless force=True.
            if rag_pipeline is not None and not force:
                print("RAG pipeline already initialized; skipping re-initialization.")
                return True

            print("Initializing RAG pipeline...")
            _emb = model_name or _default_embedding_model()
            _llm = llm_model or _default_llm_model()

            # Initialize components
            embedding_manager = EmbeddingManager(model_name=_emb)
            vector_store = VectorStore()
            retriever = RAGRetriever(vector_store, embedding_manager)
            llm = GroqLLM(model_name=_llm)
            rag_pipeline = RAGPipeline(retriever, llm)
            data_loader = DataLoader()
            
            print("✓ RAG pipeline initialized successfully")
            return True
        except Exception as e:
            print(f"✗ Error initializing pipeline: {e}")
            return False


def load_documents_to_store(data_directory: str):
    """Load documents and add to vector store."""
    global data_loader, vector_store, embedding_manager, rag_pipeline
    
    with pipeline_lock:
        try:
            if not data_loader:
                raise ValueError("DataLoader not initialized. Initialize pipeline first.")
            
            print(f"Loading documents from {data_directory}...")
            
            # Load documents
            documents = data_loader.load_all_documents(data_directory)
            
            if not documents:
                print("✗ No documents loaded")
                return False
            
            # Split documents
            split_docs = data_loader.split_documents(documents)
            
            # Generate embeddings
            texts = [doc.page_content for doc in split_docs]
            embeddings = embedding_manager.generate_embeddings(texts)
            
            # Add to vector store
            vector_store.add_documents(split_docs, embeddings)
            
            print("✓ Documents loaded and indexed successfully")
            return True
        except Exception as e:
            print(f"✗ Error loading documents: {e}")
            return False


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize pipeline on startup."""
    try:
        logger.info(f"Starting RAG Chatbot with domain: {DOMAIN_CONFIG['domain']}")
        initialize_pipeline()
        # Try to load existing documents
        data_dir = os.getenv("DATA_DIR", "./data")
        if os.path.exists(data_dir):
            logger.info(f"Found data directory at {data_dir}")
            load_documents_to_store(data_dir)
    except Exception as e:
        logger.warning(f"Startup initialization warning: {e}")
        logger.info("Pipeline can be initialized via /init endpoint")


# Endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "RAG Chatbot API",
        "version": "1.0.0",
        "endpoints": {
            "query": "/query",
            "init": "/init",
            "load-documents": "/load-documents",
            "status": "/status",
            "history": "/history",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    status = {
        "status": "healthy",
        "pipeline_initialized": rag_pipeline is not None,
        "documents_indexed": vector_store.get_collection_count() if vector_store else 0
    }
    return status


@app.post("/init")
async def initialize(request: InitializeRequest):
    """Initialize the RAG pipeline."""
    success = initialize_pipeline(
        model_name=request.model_name or _default_embedding_model(),
        llm_model=request.llm_model or _default_llm_model(),
    )
    
    if success:
        return {"status": "success", "message": "Pipeline initialized"}
    else:
        raise HTTPException(status_code=500, detail="Failed to initialize pipeline")


@app.post("/load-documents")
async def load_documents(request: DataLoadRequest, background_tasks: BackgroundTasks):
    """Load documents from directory."""
    if not os.path.exists(request.data_directory):
        raise HTTPException(status_code=400, detail="Directory not found")
    
    # Run in background to avoid timeout
    background_tasks.add_task(load_documents_to_store, request.data_directory)
    
    return {"status": "loading", "message": "Documents loading in background"}


@app.post("/query")
async def query(request: QueryRequest) -> QueryResponse:
    """Query the RAG pipeline."""
    if not rag_pipeline:
        raise HTTPException(
            status_code=503,
            detail="Pipeline not initialized. Call /init first."
        )
    
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    try:
        with pipeline_lock:
            result = rag_pipeline.query(
                question=request.question,
                top_k=request.top_k,
                min_score=request.min_score,
                return_sources=True
            )
        
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def status():
    """Get pipeline status."""
    if not vector_store:
        return {"status": "not_initialized"}
    
    return {
        "status": "ready",
        "documents_indexed": vector_store.get_collection_count(),
        "embedding_model": embedding_manager.model_name if embedding_manager else None,
        "llm_model": llm.model_name if llm else None
    }


@app.get("/history")
async def history():
    """Get query history."""
    if not rag_pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    return {
        "history": rag_pipeline.get_history(),
        "count": len(rag_pipeline.get_history())
    }


@app.post("/clear-history")
async def clear_history():
    """Clear query history."""
    if not rag_pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    rag_pipeline.clear_history()
    return {"status": "success", "message": "History cleared"}


@app.delete("/reset")
async def reset():
    """Reset the entire pipeline."""
    global rag_pipeline, vector_store, embedding_manager, retriever, llm, data_loader
    
    with pipeline_lock:
        try:
            if vector_store:
                vector_store.clear_collection()
            
            rag_pipeline = None
            vector_store = None
            embedding_manager = None
            retriever = None
            llm = None
            data_loader = None
            
            initialize_pipeline()
            return {"status": "success", "message": "Pipeline reset"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
