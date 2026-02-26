"""Data loader module for PDF and text document processing."""

import os
import logging
from pathlib import Path
from typing import List, Any

logger = logging.getLogger(__name__)

try:
    from langchain_community.document_loaders import PyPDFLoader, TextLoader
except ImportError:
    try:
        from langchain.document_loaders import PyPDFLoader, TextLoader
    except ImportError:
        logger.error("Could not import document loaders. Install with: uv pip install langchain-community")
        raise

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
    except ImportError:
        logger.error("Could not import text splitter. Install with: uv pip install langchain-text-splitters")
        raise


class DataLoader:
    """Handles loading and processing of various document types."""
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        """
        Initialize data loader with text splitting configuration.
        
        Args:
            chunk_size: Size of text chunks for splitting (default: CHUNK_SIZE env or 1000)
            chunk_overlap: Overlap between chunks (default: CHUNK_OVERLAP env or 200)
        """
        self.chunk_size = chunk_size if chunk_size is not None else int(os.environ.get("CHUNK_SIZE", "1000"))
        self.chunk_overlap = chunk_overlap if chunk_overlap is not None else int(os.environ.get("CHUNK_OVERLAP", "200"))
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def load_pdfs(self, pdf_directory: str) -> List[Any]:
        """
        Load all PDF files from a directory.
        
        Args:
            pdf_directory: Path to directory containing PDF files
            
        Returns:
            List of LangChain documents
        """
        all_documents = []
        pdf_dir = Path(pdf_directory)
        
        if not pdf_dir.exists():
            print(f"PDF directory not found: {pdf_directory}")
            return all_documents
        
        # Find all PDF files recursively
        pdf_files = list(pdf_dir.glob("**/*.pdf"))
        print(f"Found {len(pdf_files)} PDF files to process")
        
        for pdf_file in pdf_files:
            print(f"Processing: {pdf_file.name}")
            try:
                loader = PyPDFLoader(str(pdf_file))
                documents = loader.load()
            except Exception as e:
                print(f"  ✗ Error loading as PDF: {e}")
                # Fallback: some files may be mislabelled as PDF but actually
                # contain plain text. In that case, try a simple text load so
                # we can still index the content.
                try:
                    text_loader = TextLoader(str(pdf_file), encoding="utf-8")
                    documents = text_loader.load()
                    for doc in documents:
                        doc.metadata["source_file"] = pdf_file.name
                        # Mark that this came from a PDF path but was read as text
                        doc.metadata["file_type"] = "pdf_text_fallback"
                    all_documents.extend(documents)
                    print("  ✓ Loaded as plain text (fallback)")
                except Exception as text_err:
                    print(f"  ✗ Fallback text load failed: {text_err}")
                    continue

            else:
                # Add source information to metadata for successfully parsed PDFs
                for doc in documents:
                    doc.metadata["source_file"] = pdf_file.name
                    doc.metadata["file_type"] = "pdf"
                all_documents.extend(documents)
                print(f"  ✓ Loaded {len(documents)} pages")
        
        print(f"\nTotal documents loaded: {len(all_documents)}")
        return all_documents
    
    def load_text_files(self, text_directory: str) -> List[Any]:
        """
        Load all text files from a directory.
        
        Args:
            text_directory: Path to directory containing text files
            
        Returns:
            List of LangChain documents
        """
        all_documents = []
        text_dir = Path(text_directory)
        
        if not text_dir.exists():
            print(f"Text directory not found: {text_directory}")
            return all_documents
        
        # Find all text files
        text_files = list(text_dir.glob("**/*.txt"))
        print(f"Found {len(text_files)} text files to process")
        
        for text_file in text_files:
            print(f"Processing: {text_file.name}")
            try:
                loader = TextLoader(str(text_file), encoding='utf-8')
                documents = loader.load()
                
                # Add source information to metadata
                for doc in documents:
                    doc.metadata['source_file'] = text_file.name
                    doc.metadata['file_type'] = 'text'
                
                all_documents.extend(documents)
                print(f"   Loaded 1 document")
            except Exception as e:
                print(f"  Error: {e}")
        
        print(f"\nTotal documents loaded: {len(all_documents)}")
        return all_documents
    
    def load_all_documents(self, data_directory: str) -> List[Any]:
        """
        Load all documents (PDFs and text files) from a directory.
        
        Args:
            data_directory: Path to data directory
            
        Returns:
            Combined list of all documents
        """
        all_documents = []
        
        # Load PDFs
        pdf_docs = self.load_pdfs(os.path.join(data_directory, "pdf"))
        all_documents.extend(pdf_docs)
        
        # Load text files
        text_docs = self.load_text_files(os.path.join(data_directory, "text_files"))
        all_documents.extend(text_docs)
        
        return all_documents
    
    def split_documents(self, documents: List[Any]) -> List[Any]:
        """
        Split documents into smaller chunks.
        
        Args:
            documents: List of documents to split
            
        Returns:
            List of split document chunks
        """
        split_docs = self.text_splitter.split_documents(documents)
        print(f"Split {len(documents)} documents into {len(split_docs)} chunks")
        
        if split_docs:
            print(f"\nExample chunk:")
            print(f"Content: {split_docs[0].page_content[:200]}...")
            print(f"Metadata: {split_docs[0].metadata}")
        
        return split_docs
