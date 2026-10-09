"""
Vector Store Manager Module
Manages vector database operations (ChromaDB, Pinecone, FAISS)
"""
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore
from langchain_core.embeddings import Embeddings
import os

from .config import rag_config


class VectorStoreManager:
    """Manages vector store operations for RAG pipeline"""
    
    def __init__(self, embedding_model: Embeddings):
        """
        Initialize vector store manager
        
        Args:
            embedding_model: Embeddings model instance
        """
        self.embedding_model = embedding_model
        self.vector_store: Optional[VectorStore] = None
        self._initialize_vector_store()
    
    def _initialize_vector_store(self):
        """Initialize the vector store based on configuration"""
        
        if rag_config.VECTOR_STORE == "chromadb":
            self._init_chromadb()
        elif rag_config.VECTOR_STORE == "pinecone":
            self._init_pinecone()
        elif rag_config.VECTOR_STORE == "faiss":
            self._init_faiss()
        else:
            raise ValueError(f"Unsupported vector store: {rag_config.VECTOR_STORE}")
    
    def _init_chromadb(self):
        """Initialize ChromaDB vector store"""
        try:
            from langchain_community.vectorstores import Chroma
            
            # Create persist directory if it doesn't exist
            os.makedirs(rag_config.CHROMA_PERSIST_DIR, exist_ok=True)
            
            self.vector_store = Chroma(
                collection_name=rag_config.CHROMA_COLLECTION_NAME,
                embedding_function=self.embedding_model,
                persist_directory=rag_config.CHROMA_PERSIST_DIR
            )
            print(f"[OK] ChromaDB initialized at {rag_config.CHROMA_PERSIST_DIR}")
        except Exception as e:
            print(f"[FAIL] Failed to initialize ChromaDB: {e}")
            raise
    
    def _init_pinecone(self):
        """Initialize Pinecone vector store"""
        try:
            from langchain_community.vectorstores import Pinecone
            from pinecone import Pinecone as PineconeClient, ServerlessSpec
            
            if not rag_config.PINECONE_API_KEY:
                raise ValueError("PINECONE_API_KEY not configured")
            
            # Initialize Pinecone client
            pc = PineconeClient(api_key=rag_config.PINECONE_API_KEY)
            
            # Create index if it doesn't exist
            index_name = rag_config.PINECONE_INDEX_NAME
            if index_name not in pc.list_indexes().names():
                pc.create_index(
                    name=index_name,
                    dimension=rag_config.EMBEDDING_DIMENSION,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=rag_config.PINECONE_ENVIRONMENT
                    )
                )
            
            # Connect to index
            index = pc.Index(index_name)
            
            self.vector_store = Pinecone(
                index=index,
                embedding=self.embedding_model,
                text_key="text"
            )
            print(f"[OK] Pinecone initialized with index: {index_name}")
        except Exception as e:
            print(f"[FAIL] Failed to initialize Pinecone: {e}")
            raise
    
    def _init_faiss(self):
        """Initialize FAISS vector store"""
        try:
            from langchain_community.vectorstores import FAISS
            
            index_path = rag_config.FAISS_INDEX_PATH
            
            # Load existing index if available
            if os.path.exists(index_path):
                self.vector_store = FAISS.load_local(
                    index_path,
                    self.embedding_model,
                    allow_dangerous_deserialization=True
                )
                print(f"[OK] FAISS index loaded from {index_path}")
            else:
                # Create empty store - will be populated later
                self.vector_store = None
                print(f"[OK] FAISS will be initialized on first document add")
        except Exception as e:
            print(f"[FAIL] Failed to initialize FAISS: {e}")
            raise
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        Add documents to vector store
        
        Args:
            documents: List of Document objects to add
        
        Returns:
            List of document IDs
        """
        if not documents:
            return []
        
        try:
            if rag_config.VECTOR_STORE == "faiss" and self.vector_store is None:
                # Initialize FAISS with first batch of documents
                from langchain_community.vectorstores import FAISS
                self.vector_store = FAISS.from_documents(
                    documents,
                    self.embedding_model
                )
                print(f"[OK] FAISS initialized with {len(documents)} documents")
            else:
                ids = self.vector_store.add_documents(documents)
                print(f"[OK] Added {len(documents)} documents to vector store")
                return ids

            return [str(i) for i in range(len(documents))]
        except Exception as e:
            print(f"[FAIL] Error adding documents: {e}")
            raise
    
    def similarity_search(
        self,
        query: str,
        k: int = None,
        filter: Dict[str, Any] = None
    ) -> List[Document]:
        """
        Search for similar documents
        
        Args:
            query: Search query
            k: Number of results to return
            filter: Metadata filters
        
        Returns:
            List of similar documents
        """
        if self.vector_store is None:
            return []
        
        k = k or rag_config.RETRIEVAL_TOP_K
        
        try:
            if filter:
                results = self.vector_store.similarity_search(
                    query,
                    k=k,
                    filter=filter
                )
            else:
                results = self.vector_store.similarity_search(query, k=k)
            
            return results
        except Exception as e:
            print(f"[FAIL] Error in similarity search: {e}")
            return []
    
    def similarity_search_with_score(
        self,
        query: str,
        k: int = None,
        filter: Dict[str, Any] = None
    ) -> List[tuple[Document, float]]:
        """
        Search with similarity scores
        
        Args:
            query: Search query
            k: Number of results
            filter: Metadata filters
        
        Returns:
            List of (document, score) tuples
        """
        if self.vector_store is None:
            return []
        
        k = k or rag_config.RETRIEVAL_TOP_K
        
        try:
            results = self.vector_store.similarity_search_with_score(
                query,
                k=k,
                filter=filter
            )
            
            # Filter by similarity threshold
            filtered_results = [
                (doc, score) for doc, score in results
                if score >= rag_config.SIMILARITY_THRESHOLD
            ]
            
            return filtered_results
        except Exception as e:
            print(f"[FAIL] Error in similarity search with score: {e}")
            return []
    
    def delete_collection(self):
        """Delete the entire collection"""
        try:
            if rag_config.VECTOR_STORE == "chromadb":
                self.vector_store.delete_collection()
                print("[OK] ChromaDB collection deleted")
            elif rag_config.VECTOR_STORE == "faiss":
                import shutil
                if os.path.exists(rag_config.FAISS_INDEX_PATH):
                    shutil.rmtree(rag_config.FAISS_INDEX_PATH)
                print("[OK] FAISS index deleted")
            else:
                print("[WARN] Delete not implemented for this vector store")
        except Exception as e:
            print(f"[FAIL] Error deleting collection: {e}")
    
    def persist(self):
        """Persist the vector store to disk"""
        try:
            if rag_config.VECTOR_STORE == "chromadb":
                self.vector_store.persist()
                print("[OK] ChromaDB persisted")
            elif rag_config.VECTOR_STORE == "faiss":
                if self.vector_store:
                    os.makedirs(os.path.dirname(rag_config.FAISS_INDEX_PATH), exist_ok=True)
                    self.vector_store.save_local(rag_config.FAISS_INDEX_PATH)
                    print(f"[OK] FAISS index saved to {rag_config.FAISS_INDEX_PATH}")
        except Exception as e:
            print(f"[FAIL] Error persisting vector store: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        try:
            if rag_config.VECTOR_STORE == "chromadb":
                collection = self.vector_store._collection
                return {
                    "vector_store": "chromadb",
                    "collection_name": rag_config.CHROMA_COLLECTION_NAME,
                    "document_count": collection.count()
                }
            elif rag_config.VECTOR_STORE == "faiss":
                if self.vector_store:
                    return {
                        "vector_store": "faiss",
                        "index_path": rag_config.FAISS_INDEX_PATH,
                        "document_count": self.vector_store.index.ntotal
                    }
            elif rag_config.VECTOR_STORE == "pinecone":
                return {
                    "vector_store": "pinecone",
                    "index_name": rag_config.PINECONE_INDEX_NAME
                }
            
            return {"vector_store": rag_config.VECTOR_STORE}
        except Exception as e:
            return {"error": str(e)}
