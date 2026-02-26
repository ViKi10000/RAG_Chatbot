"""LLM integration module using Groq."""

import os
from typing import Optional

try:
    from langchain_groq import ChatGroq
except ImportError:
    try:
        from langchain.chat_models.groq import ChatGroq
    except ImportError:
        raise ImportError(
            "Could not import ChatGroq. "
            "Install with: uv pip install langchain-groq"
        )

try:
    from langchain_core.messages import HumanMessage, BaseMessage
except ImportError:
    from langchain.schema import HumanMessage, BaseMessage


class GroqLLM:
    """Groq LLM wrapper for response generation."""
    
    def __init__(
        self,
        model_name: str = "llama-3.1-8b-instant",
        api_key: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 256
    ):
        """
        Initialize Groq LLM.
        
        Args:
            model_name: Groq model name
            api_key: Groq API key (or set GROQ_API_KEY environment variable)
            temperature: Temperature for response generation
            max_tokens: Maximum tokens in response
        """
        # Allow overriding the model via environment variable so we
        # can react to future deprecations without code changes.
        env_model = os.environ.get("GROQ_LLM_MODEL")
        self.model_name = env_model or model_name
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        if not self.api_key:
            raise ValueError(
                "Groq API key is required. "
                "Set GROQ_API_KEY environment variable or pass api_key parameter."
            )
        
        self.llm = ChatGroq(
            groq_api_key=self.api_key,
            model_name=self.model_name,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        print(f"✓ Initialized Groq LLM: {self.model_name}")
    
    def generate_response(
        self,
        query: str,
        context: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate response using retrieved context.
        
        Args:
            query: User question
            context: Retrieved document context
            system_prompt: Custom system prompt
            
        Returns:
            Generated response string
        """
        
        if not context or not context.strip():
            return "No context about this question."
        
        # Default system prompt focused on strict grounding and brevity,
        # but still allowing answers when the context clearly contains
        # relevant information (even if it is not phrased exactly like
        # the question).
        if not system_prompt:
            system_prompt = (
                "You are a retrieval-augmented assistant.\n"
                "You must answer only using the information in the Context section.\n"
                "If the context contains information that can reasonably answer the question "
                "(even if wording is slightly different), use it to answer.\n"
                "If the context does not contain any information that can help answer the question,\n"
                'reply exactly with: \"No context about this question.\".\n'
                "Keep answers short and focused (1–3 sentences). Do not add introductions or closing remarks.\n"
                "Never guess, speculate, or use outside knowledge beyond the provided context."
            )
        
        # Create prompt
        prompt = f"""{system_prompt}

Context:
{context}

Question: {query}

Answer:"""
        
        try:
            messages = [HumanMessage(content=prompt)]
            response = self.llm.invoke(messages)
            return response.content
            
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def generate_simple_response(self, query: str, context: str) -> str:
        """
        Generate a simple response without complex prompting.
        
        Args:
            query: User question
            context: Retrieved context
            
        Returns:
            Generated response
        """
        if not context or not context.strip():
            return "No context about this question."
        
        simple_prompt = f"""Based on this context: {context}

Question: {query}

Answer concisely:"""
        
        try:
            messages = [HumanMessage(content=simple_prompt)]
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            return f"Error: {str(e)}"


class RAGPipeline:
    """Complete RAG pipeline integrating retrieval and generation."""
    
    def __init__(self, retriever, llm: GroqLLM):
        """
        Initialize RAG pipeline.
        
        Args:
            retriever: RAGRetriever instance
            llm: GroqLLM instance
        """
        self.retriever = retriever
        self.llm = llm
        self.query_history = []
    
    def query(
        self,
        question: str,
        top_k: int = 5,
        min_score: float = 0.2,
        return_sources: bool = True
    ) -> dict:
        """
        Execute a complete RAG query.
        
        Args:
            question: User question
            top_k: Number of documents to retrieve
            min_score: Minimum similarity score threshold
            return_sources: Whether to return source information
            
        Returns:
            Dictionary with answer, sources, and metadata
        """
        
        # Retrieve context
        retrieval_result = self.retriever.retrieve_with_context(
            question,
            top_k=top_k,
            score_threshold=min_score,
        )

        context = retrieval_result["context"]
        documents = retrieval_result["documents"]

        # If we have no documents at all, do not call the LLM.
        # This guarantees we never answer without supporting context.
        if not documents:
            answer = "No context about this question."
        else:
            answer = self.llm.generate_response(question, context)
        
        # Prepare response
        response = {
            "question": question,
            "answer": answer,
            "document_count": len(documents),
            "confidence": max([doc["similarity_score"] for doc in documents])
            if documents
            else 0.0,
        }
        
        if return_sources:
            response["sources"] = [
                {
                    "source": doc["metadata"].get("source_file", "unknown"),
                    "page": doc["metadata"].get("page", "N/A"),
                    "similarity_score": doc["similarity_score"],
                    "preview": (
                        doc["content"][:200] + "..."
                        if len(doc["content"]) > 200
                        else doc["content"]
                    ),
                }
                for doc in documents
            ]
        
        # Store in history
        self.query_history.append(response)
        
        return response
    
    def get_history(self) -> list:
        """Get query history."""
        return self.query_history
    
    def clear_history(self):
        """Clear query history."""
        self.query_history = []
