"""Search and retrieval module for RAG pipeline."""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

from src.embedding import EmbeddingManager
from src.vectorstore import VectorStore


class RAGRetriever:
    """Handles query-based retrieval from the vector store."""
    
    def __init__(
        self,
        vector_store: VectorStore,
        embedding_manager: EmbeddingManager
    ):
        """
        Initialize the retriever.
        
        Args:
            vector_store: Vector store containing document embeddings
            embedding_manager: Manager for generating query embeddings
        """
        self.vector_store = vector_store
        self.embedding_manager = embedding_manager
    
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: The search query
            top_k: Number of top results to return
            score_threshold: Minimum similarity score threshold
            
        Returns:
            List of dictionaries containing retrieved documents and metadata
        """
        print(f"\n'Retrieving documents for: \"{query}\"")
        print(f"  Top K: {top_k}, Score threshold: {score_threshold}")

        # Generate query embedding
        query_embedding = self.embedding_manager.generate_embedding(query)

        # Search in vector store
        try:
            results = self.vector_store.search(query_embedding, top_k=top_k)

            # Process results
            retrieved_docs = []

            if results and results.get('documents') and results['documents'][0]:
                documents = results['documents'][0]
                metadatas = results['metadatas'][0]
                distances = results['distances'][0]
                ids = results['ids'][0]

                all_docs = []

                for i, (doc_id, document, metadata, distance) in enumerate(
                    zip(ids, documents, metadatas, distances)
                ):
                    # Convert distance to similarity score (ChromaDB uses cosine distance)
                    similarity_score = 1 - distance

                    doc_info = {
                        'id': doc_id,
                        'content': document,
                        'metadata': metadata,
                        'similarity_score': similarity_score,
                        'distance': distance,
                        'rank': i + 1
                    }
                    all_docs.append(doc_info)

                # Apply score threshold if provided
                if score_threshold and score_threshold > 0:
                    retrieved_docs = [
                        doc for doc in all_docs
                        if doc['similarity_score'] >= score_threshold
                    ]
                else:
                    retrieved_docs = all_docs

                # Fallback: if threshold filtered everything out but we had results,
                # return the top_k documents without thresholding so the user still
                # gets some context instead of an empty answer.
                if not retrieved_docs and all_docs:
                    print(
                        "No documents passed the score threshold; "
                        "returning top results without thresholding instead."
                    )
                    retrieved_docs = all_docs[:top_k]

                print(f" Retrieved {len(retrieved_docs)} documents")
            else:
                print("No documents found")

            return retrieved_docs

        except Exception as e:
            print(f" Error during retrieval: {e}")
            return []
    
    def retrieve_with_context(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.0
    ) -> Dict[str, Any]:
        """
        Retrieve documents and prepare context string.
        
        Args:
            query: The search query
            top_k: Number of top results to return
            score_threshold: Minimum similarity score threshold
            
        Returns:
            Dictionary with retrieved documents and formatted context
        """
        docs = self.retrieve(query, top_k, score_threshold)
        
        # Prepare context string
        context = "\n\n".join([doc['content'] for doc in docs]) if docs else ""
        
        # Prepare sources
        sources = [
            {
                'source': doc['metadata'].get('source_file', 'unknown'),
                'page': doc['metadata'].get('page', 'N/A'),
                'score': doc['similarity_score']
            }
            for doc in docs
        ]
        
        return {
            'documents': docs,
            'context': context,
            'sources': sources,
            'document_count': len(docs)
        }
