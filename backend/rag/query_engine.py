"""
RAG Query Engine Module
Handles query processing, retrieval, and LLM-based generation
"""
from typing import List, Dict, Any, Optional
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document

from .config import rag_config
from .vector_store import VectorStoreManager
from .document_processor import DocumentProcessor


class RAGQueryEngine:
    """RAG Query Engine for contextual insights"""
    
    def __init__(
        self,
        embedding_model: Embeddings,
        llm_model: BaseChatModel
    ):
        """
        Initialize RAG query engine
        
        Args:
            embedding_model: Embeddings model for vector search
            llm_model: Language model for generation
        """
        self.embedding_model = embedding_model
        self.llm_model = llm_model
        self.vector_store_manager = VectorStoreManager(embedding_model)
        self.document_processor = DocumentProcessor()
        
        # Initialize RAG chain
        self._setup_rag_chain()
    
    def _setup_rag_chain(self):
        """Setup the RAG chain with custom prompt"""
        
        # Custom prompt template for market trends and sentiment analysis
        prompt_template = """You are an AI assistant specializing in consumer sentiment analysis and market trends.

Use the following context from product reviews, news articles, and market data to answer the question.
Provide specific insights, sentiment trends, and actionable intelligence for marketing and product teams.

Context:
{context}

Question: {question}

Answer: Provide a detailed, data-driven response based on the context above. Include:
1. Direct answer to the question
2. Relevant sentiment trends and patterns
3. Key insights from the data
4. Actionable recommendations if applicable

If the context doesn't contain enough information, say so and provide general guidance.

Answer:"""

        self.PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
    
    def query(
        self,
        question: str,
        filters: Optional[Dict[str, Any]] = None,
        return_sources: bool = True
    ) -> Dict[str, Any]:
        """
        Query the RAG system
        
        Args:
            question: User question
            filters: Metadata filters (e.g., category, sentiment)
            return_sources: Whether to return source documents
        
        Returns:
            Dictionary with answer and optional sources
        """
        if not self.vector_store_manager.vector_store:
            return {
                "question": question,
                "answer": "RAG system not initialized. Please index documents first.",
                "sources": [],
                "success": False,
                "error": "No documents indexed"
            }
        
        try:
            # Get relevant documents
            docs = self.vector_store_manager.similarity_search(
                query=question,
                k=rag_config.RETRIEVAL_TOP_K
            )
            
            if not docs:
                return {
                    "question": question,
                    "answer": "No relevant information found in the knowledge base.",
                    "sources": [],
                    "success": False
                }
            
            # Build context
            context = "\n\n".join([doc.page_content for doc in docs])
            
            # Generate answer
            prompt = self.PROMPT.format(context=context, question=question)
            answer = self.llm_model.invoke(prompt)
            
            # Extract content (handle different response types)
            if hasattr(answer, 'content'):
                answer_text = answer.content
            else:
                answer_text = str(answer)
            
            response = {
                "question": question,
                "answer": answer_text,
                "success": True
            }
            
            if return_sources:
                sources = []
                for doc in docs:
                    sources.append({
                        "content": doc.page_content[:200] + "...",
                        "metadata": doc.metadata
                    })
                response["sources"] = sources
                response["source_count"] = len(sources)
            
            return response
            
        except Exception as e:
            return {
                "question": question,
                "answer": f"Error processing query: {str(e)}",
                "success": False,
                "error": str(e)
            }
    
    def query_with_filters(
        self,
        question: str,
        category: Optional[str] = None,
        sentiment: Optional[str] = None,
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Query with metadata filters
        
        Args:
            question: User question
            category: Filter by product category
            sentiment: Filter by sentiment (Positive, Negative, Neutral)
            date_range: Date range filter
        
        Returns:
            Query response
        """
        # Retrieve relevant documents with filters
        filter_dict = {}
        if category:
            filter_dict["category"] = category
        if sentiment:
            filter_dict["sentiment"] = sentiment
        
        # Get relevant documents
        docs = self.vector_store_manager.similarity_search(
            query=question,
            k=rag_config.RETRIEVAL_TOP_K,
            filter=filter_dict if filter_dict else None
        )
        
        if not docs:
            return {
                "question": question,
                "answer": "No relevant documents found with the specified filters.",
                "sources": [],
                "filters_applied": filter_dict
            }
        
        # Build context from documents
        context = "\n\n".join([doc.page_content for doc in docs])
        
        # Generate answer using LLM
        prompt = self.PROMPT.format(context=context, question=question)
        
        try:
            answer_response = self.llm_model.invoke(prompt)
            
            # Extract content
            if hasattr(answer_response, 'content'):
                answer = answer_response.content
            else:
                answer = str(answer_response)
            
            return {
                "question": question,
                "answer": answer,
                "sources": [{"content": doc.page_content[:200] + "...", "metadata": doc.metadata} for doc in docs],
                "source_count": len(docs),
                "filters_applied": filter_dict,
                "success": True
            }
        except Exception as e:
            return {
                "question": question,
                "answer": f"Error generating response: {str(e)}",
                "success": False,
                "error": str(e)
            }
    
    def get_sentiment_summary(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Get sentiment summary for a category
        
        Args:
            category: Product category
        
        Returns:
            Sentiment summary
        """
        question = f"What is the overall sentiment trend for {category if category else 'all products'}? Provide statistics and key insights."
        return self.query(question)
    
    def get_trending_topics(self, limit: int = 5) -> Dict[str, Any]:
        """
        Get trending topics from the data
        
        Args:
            limit: Number of topics to return
        
        Returns:
            Trending topics
        """
        question = f"What are the top {limit} trending topics or themes in consumer discussions? List them with brief descriptions."
        return self.query(question)
    
    def compare_products(self, categories: List[str]) -> Dict[str, Any]:
        """
        Compare sentiment across multiple categories
        
        Args:
            categories: List of categories to compare
        
        Returns:
            Comparison results
        """
        question = f"Compare consumer sentiment and feedback across these categories: {', '.join(categories)}. Highlight key differences and insights."
        return self.query(question)
    
    def get_contextual_insights(
        self,
        query: str,
        context_type: str = "all"
    ) -> Dict[str, Any]:
        """
        Get contextual insights based on query
        
        Args:
            query: User query
            context_type: Type of context (reviews, news, all)
        
        Returns:
            Contextual insights
        """
        filter_dict = {}
        if context_type == "reviews":
            filter_dict["doc_type"] = "review"
        elif context_type == "news":
            filter_dict["doc_type"] = "news"
        
        docs = self.vector_store_manager.similarity_search(
            query=query,
            k=rag_config.RETRIEVAL_TOP_K,
            filter=filter_dict if filter_dict else None
        )
        
        if not docs:
            return {
                "query": query,
                "insights": "No relevant data found.",
                "sources": []
            }
        
        # Build enhanced question
        enhanced_question = f"""Based on the available data, provide detailed insights about: {query}
        
        Include:
        - Key patterns and trends
        - Sentiment analysis
        - Consumer behavior insights
        - Actionable recommendations for marketing teams"""
        
        context = "\n\n".join([doc.page_content for doc in docs])
        prompt = self.PROMPT.format(context=context, question=enhanced_question)
        
        try:
            response = self.llm_model.invoke(prompt)
            
            # Extract content
            if hasattr(response, 'content'):
                insights = response.content
            else:
                insights = str(response)
            
            return {
                "query": query,
                "insights": insights,
                "sources": [{"content": doc.page_content[:150] + "...", "metadata": doc.metadata} for doc in docs],
                "source_count": len(docs),
                "context_type": context_type
            }
        except Exception as e:
            return {
                "query": query,
                "insights": f"Error generating insights: {str(e)}",
                "error": str(e)
            }
    
    def index_documents(self, documents: List[Document]) -> Dict[str, Any]:
        """
        Index documents into vector store
        
        Args:
            documents: List of documents to index
        
        Returns:
            Indexing results
        """
        try:
            ids = self.vector_store_manager.add_documents(documents)
            self.vector_store_manager.persist()
            
            return {
                "success": True,
                "indexed_count": len(documents),
                "document_ids": ids
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get RAG system statistics"""
        return {
            "vector_store": self.vector_store_manager.get_stats(),
            "config": {
                "llm_provider": rag_config.LLM_PROVIDER,
                "llm_model": rag_config.GROQ_MODEL if rag_config.LLM_PROVIDER == "groq" else rag_config.OPENAI_MODEL,
                "embedding_provider": rag_config.EMBEDDING_PROVIDER,
                "embedding_model": rag_config.EMBEDDING_MODEL,
                "vector_store_type": rag_config.VECTOR_STORE,
                "retrieval_top_k": rag_config.RETRIEVAL_TOP_K
            }
        }
