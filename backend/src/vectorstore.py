"""Vector store management using ChromaDB."""

import os
import uuid
import logging
import numpy as np
from typing import List, Any, Dict

logger = logging.getLogger(__name__)

try:
    import chromadb
except ImportError:
    logger.error("Could not import chromadb. Install with: uv pip install chromadb")
    raise


class VectorStore:
    """Manages document embeddings in a ChromaDB vector store."""
    
    def __init__(
        self,
        collection_name: str = "documents",
        persist_directory: str = "./data/vector_store"
    ):
        """
        Initialize the vector store.
        
        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory to persist the vector store
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None
        self._initialize_store()
    
    def _initialize_store(self):
        """Initialize ChromaDB client and collection."""
        try:
            # Create persistent ChromaDB client
            os.makedirs(self.persist_directory, exist_ok=True)
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "RAG document embeddings"}
            )
            print(f" Vector store initialized")
            print(f"  Collection: {self.collection_name}")
            print(f"  Existing documents: {self.collection.count()}")
            
        except Exception as e:
            print(f" Error initializing vector store: {e}")
            raise
    
    def add_documents(self, documents: List[Any], embeddings: np.ndarray):
        """
        Add documents and their embeddings to the vector store.
        
        Args:
            documents: List of LangChain documents
            embeddings: Corresponding embeddings for the documents
        """
        if len(documents) != len(embeddings):
            raise ValueError("Number of documents must match number of embeddings")
        
        print(f"Adding {len(documents)} documents to vector store...")
        
        # Prepare data for ChromaDB
        ids = []
        metadatas = []
        documents_text = []
        embeddings_list = []
        
        for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
            # Generate unique ID
            doc_id = f"doc_{uuid.uuid4().hex[:8]}_{i}"
            ids.append(doc_id)
            
            # Prepare metadata
            metadata = dict(doc.metadata) if hasattr(doc, 'metadata') else {}
            metadata['doc_index'] = i
            metadata['content_length'] = len(doc.page_content)
            metadatas.append(metadata)
            
            # Document content
            documents_text.append(doc.page_content)
            
            # Embedding
            embeddings_list.append(embedding.tolist())
        
        # Add to collection
        try:
            self.collection.add(
                ids=ids,
                embeddings=embeddings_list,
                metadatas=metadatas,
                documents=documents_text
            )
            print(f" Successfully added {len(documents)} documents")
            print(f"  Total documents in collection: {self.collection.count()}")
            
        except Exception as e:
            print(f" Error adding documents: {e}")
            raise
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Search for similar documents using embedding.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of top results to return
            
        Returns:
            Dictionary with search results
        """
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k
            )
            return results
        except Exception as e:
            print(f" Error searching vector store: {e}")
            return {}
    
    def get_collection_count(self) -> int:
        """Get the number of documents in the collection."""
        return self.collection.count()
    
    def clear_collection(self):
        """Clear all documents from the collection."""
        try:
            # Delete the current collection and recreate it
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "RAG document embeddings"}
            )
            print(" Collection cleared successfully")
        except Exception as e:
            print(f" Error clearing collection: {e}")
            raise
