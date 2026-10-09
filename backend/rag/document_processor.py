"""
Document Processor Module
Handles document loading, cleaning, chunking, and preparation for RAG pipeline
"""
from typing import List, Dict, Any, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from datetime import datetime
import pandas as pd
from .config import rag_config


class DocumentProcessor:
    """Process and chunk documents for RAG pipeline"""
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None
    ):
        """
        Initialize document processor
        
        Args:
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
        """
        self.chunk_size = chunk_size or rag_config.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or rag_config.CHUNK_OVERLAP
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def process_review(
        self,
        review_text: str,
        metadata: Dict[str, Any]
    ) -> List[Document]:
        """
        Process a single review into chunks
        
        Args:
            review_text: Review text content
            metadata: Additional metadata (category, product_url, sentiment, etc.)
        
        Returns:
            List of Document objects
        """
        # Create enriched metadata
        doc_metadata = {
            "source": "product_review",
            "category": metadata.get("category", "unknown"),
            "product_url": metadata.get("product_url", ""),
            "sentiment": metadata.get("sentiment_label", ""),
            "confidence": metadata.get("confidence_score", 0),
            "timestamp": metadata.get("timestamp", datetime.now().isoformat()),
            "doc_type": "review"
        }
        
        # Create LangChain Document
        doc = Document(
            page_content=review_text,
            metadata=doc_metadata
        )
        
        # Split into chunks (if needed)
        if len(review_text) > self.chunk_size:
            chunks = self.text_splitter.split_documents([doc])
        else:
            chunks = [doc]
        
        return chunks
    
    def process_news_article(
        self,
        title: str,
        description: str,
        metadata: Dict[str, Any]
    ) -> List[Document]:
        """
        Process a news article into chunks
        
        Args:
            title: Article title
            description: Article description/content
            metadata: Additional metadata
        
        Returns:
            List of Document objects
        """
        # Combine title and description
        content = f"Title: {title}\n\nContent: {description}"
        
        # Create enriched metadata
        doc_metadata = {
            "source": "news",
            "keyword": metadata.get("keyword", ""),
            "title": title,
            "sentiment": metadata.get("sentiment_label", ""),
            "sentiment_score": metadata.get("sentiment_score", 0),
            "published_date": metadata.get("published_date", ""),
            "timestamp": metadata.get("timestamp", datetime.now().isoformat()),
            "doc_type": "news"
        }
        
        # Create LangChain Document
        doc = Document(
            page_content=content,
            metadata=doc_metadata
        )
        
        # Split into chunks
        if len(content) > self.chunk_size:
            chunks = self.text_splitter.split_documents([doc])
        else:
            chunks = [doc]
        
        return chunks
    
    def process_batch_from_mongodb(
        self,
        documents: List[Dict[str, Any]],
        doc_type: str = "review"
    ) -> List[Document]:
        """
        Process a batch of documents from MongoDB
        
        Args:
            documents: List of document dictionaries from MongoDB
            doc_type: Type of document ("review" or "news")
        
        Returns:
            List of chunked Document objects
        """
        all_chunks = []
        
        for doc in documents:
            try:
                if doc_type == "review":
                    chunks = self.process_review(
                        review_text=doc.get("review", ""),
                        metadata={
                            "category": doc.get("category", ""),
                            "product_url": doc.get("product_url", ""),
                            "sentiment_label": doc.get("sentiment_label", ""),
                            "confidence_score": doc.get("confidence_score", 0),
                        }
                    )
                elif doc_type == "news":
                    chunks = self.process_news_article(
                        title=doc.get("title", ""),
                        description=doc.get("description", ""),
                        metadata={
                            "keyword": doc.get("keyword", ""),
                            "sentiment_label": doc.get("sentiment_label", ""),
                            "sentiment_score": doc.get("sentiment_score", 0),
                            "published_date": doc.get("published_date", ""),
                        }
                    )
                else:
                    continue
                
                all_chunks.extend(chunks)
            except Exception as e:
                print(f"Error processing document: {e}")
                continue
        
        return all_chunks
    
    def process_csv(self, csv_path: str, doc_type: str = "review") -> List[Document]:
        """
        Process documents from CSV file
        
        Args:
            csv_path: Path to CSV file
            doc_type: Type of document
        
        Returns:
            List of chunked Document objects
        """
        try:
            df = pd.read_csv(csv_path)
            documents = df.to_dict('records')
            return self.process_batch_from_mongodb(documents, doc_type)
        except Exception as e:
            print(f"Error processing CSV: {e}")
            return []
    
    def create_summary_document(
        self,
        content: str,
        doc_type: str,
        metadata: Dict[str, Any]
    ) -> Document:
        """
        Create a summary document without chunking
        
        Args:
            content: Document content
            doc_type: Type of document
            metadata: Document metadata
        
        Returns:
            Single Document object
        """
        doc_metadata = {
            "source": doc_type,
            "timestamp": datetime.now().isoformat(),
            **metadata
        }
        
        return Document(
            page_content=content,
            metadata=doc_metadata
        )
