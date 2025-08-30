"""
RAG (Retrieval Augmented Generation) service for HSA Q&A system.

This service implements semantic search over HSA knowledge base documents
and generates accurate responses with proper citations as required by user stories.

Key Features:
- Vector embedding-based document search using OpenAI text-embedding-3-large
- GPT-4o-mini powered response generation with citations
- Knowledge base management and indexing
- Citation accuracy and relevance scoring
"""

import os
import json
import hashlib
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from openai import AsyncOpenAI
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from ..schemas.hsa_assistant import (
    QARequest, QAResponse, Citation, VectorSearchRequest, VectorSearchResult,
    KnowledgeBaseDocument, KnowledgeBaseStats, RAGMetrics
)


logger = logging.getLogger(__name__)


class RAGServiceError(Exception):
    """Exception raised during RAG service operations."""
    pass


class VectorStore:
    """Simple in-memory vector store for prototyping."""
    
    def __init__(self):
        """Initialize empty vector store."""
        self.embeddings: Dict[str, np.ndarray] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self.documents: Dict[str, str] = {}
    
    async def store(self, chunk_id: str, embedding: np.ndarray, metadata: Dict[str, Any]):
        """Store embedding with metadata."""
        self.embeddings[chunk_id] = embedding
        self.metadata[chunk_id] = metadata
        if 'text' in metadata:
            self.documents[chunk_id] = metadata['text']
    
    async def similarity_search(
        self, 
        query_embedding: np.ndarray, 
        k: int = 5, 
        threshold: float = 0.7
    ) -> List[Tuple[str, float]]:
        """Find k most similar embeddings above threshold."""
        if not self.embeddings:
            return []
        
        similarities = []
        for chunk_id, embedding in self.embeddings.items():
            similarity = cosine_similarity([query_embedding], [embedding])[0][0]
            if similarity >= threshold:
                similarities.append((chunk_id, similarity))
        
        # Sort by similarity descending and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:k]
    
    def get_chunk_count(self) -> int:
        """Get total number of chunks in store."""
        return len(self.embeddings)
    
    def get_metadata(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a chunk."""
        return self.metadata.get(chunk_id)


class DocumentChunker:
    """Utility for splitting documents into chunks for embedding."""
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        """
        Initialize chunker.
        
        Args:
            chunk_size: Maximum characters per chunk
            overlap: Number of overlapping characters between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_document(self, text: str, document_name: str) -> List[Dict[str, Any]]:
        """
        Split document into overlapping chunks.
        
        Args:
            text: Document text content
            document_name: Name of the source document
            
        Returns:
            List of chunk metadata dictionaries
        """
        chunks = []
        
        # Split by paragraphs first to maintain semantic boundaries
        paragraphs = text.split('\n\n')
        current_chunk = ""
        chunk_index = 0
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size, start new chunk
            if len(current_chunk) + len(paragraph) > self.chunk_size and current_chunk:
                chunk_id = f"{document_name}_chunk_{chunk_index}"
                chunks.append({
                    'id': chunk_id,
                    'text': current_chunk.strip(),
                    'document': document_name,
                    'chunk_index': chunk_index,
                    'char_count': len(current_chunk)
                })
                
                # Start new chunk with overlap from previous chunk
                if len(current_chunk) > self.overlap:
                    current_chunk = current_chunk[-self.overlap:] + "\n\n" + paragraph
                else:
                    current_chunk = paragraph
                
                chunk_index += 1
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Add final chunk if there's remaining content
        if current_chunk.strip():
            chunk_id = f"{document_name}_chunk_{chunk_index}"
            chunks.append({
                'id': chunk_id,
                'text': current_chunk.strip(),
                'document': document_name,
                'chunk_index': chunk_index,
                'char_count': len(current_chunk)
            })
        
        return chunks


class RAGService:
    """
    RAG service for HSA Q&A system.
    
    Implements semantic search and response generation with citations
    as specified in US-4.1 and US-4.2 user stories.
    """
    
    def __init__(self, knowledge_base_path: str = "data/knowledge_base"):
        """
        Initialize RAG service.
        
        Args:
            knowledge_base_path: Path to knowledge base documents
        """
        self.knowledge_base_path = Path(knowledge_base_path)
        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.embedding_model = "text-embedding-3-large"
        self.response_model = "gpt-4o-mini-2024-07-18"
        
        # Initialize components
        self.vector_store = VectorStore()
        self.chunker = DocumentChunker()
        self.knowledge_base_index: Dict[str, KnowledgeBaseDocument] = {}
        
        # Performance tracking
        self.query_count = 0
        self.total_response_time = 0.0
        self.confidence_scores = []
        
        logger.info(f"RAG service initialized with knowledge base: {self.knowledge_base_path}")
    
    async def build_knowledge_base(self) -> None:
        """
        Build vector embeddings for all documents in knowledge base.
        
        Implements requirements from US-4.2: Knowledge Base Management.
        """
        try:
            if not self.knowledge_base_path.exists():
                raise RAGServiceError(f"Knowledge base path does not exist: {self.knowledge_base_path}")
            
            document_files = list(self.knowledge_base_path.glob("*.txt"))
            if not document_files:
                raise RAGServiceError("No .txt files found in knowledge base directory")
            
            logger.info(f"Building knowledge base from {len(document_files)} documents")
            
            for doc_path in document_files:
                await self._process_document(doc_path)
            
            logger.info(f"Knowledge base built successfully. Total chunks: {self.vector_store.get_chunk_count()}")
            
        except Exception as e:
            logger.error(f"Failed to build knowledge base: {str(e)}")
            raise RAGServiceError(f"Knowledge base construction failed: {str(e)}")
    
    async def _process_document(self, doc_path: Path) -> None:
        """Process a single document: chunk, embed, and store."""
        try:
            # Read document content
            with open(doc_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            document_name = doc_path.name
            logger.info(f"Processing document: {document_name}")
            
            # Create chunks
            chunks = self.chunker.chunk_document(content, document_name)
            
            # Generate embeddings for each chunk
            for chunk in chunks:
                embedding = await self._create_embedding(chunk['text'])
                await self.vector_store.store(
                    chunk['id'],
                    embedding,
                    {
                        'text': chunk['text'],
                        'document': chunk['document'],
                        'chunk_index': chunk['chunk_index'],
                        'char_count': chunk['char_count']
                    }
                )
            
            # Store document metadata
            self.knowledge_base_index[document_name] = KnowledgeBaseDocument(
                id=document_name,
                name=document_name,
                title=document_name.replace('_', ' ').replace('.txt', ''),
                content_length=len(content),
                chunk_count=len(chunks),
                last_updated=datetime.fromtimestamp(doc_path.stat().st_mtime),
                created_at=datetime.utcnow()
            )
            
            logger.info(f"Processed {document_name}: {len(chunks)} chunks created")
            
        except Exception as e:
            logger.error(f"Failed to process document {doc_path}: {str(e)}")
            raise RAGServiceError(f"Document processing failed: {str(e)}")
    
    async def _create_embedding(self, text: str) -> np.ndarray:
        """Create vector embedding for text using OpenAI API."""
        try:
            response = await self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text,
                encoding_format="float"
            )
            
            embedding = np.array(response.data[0].embedding)
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to create embedding: {str(e)}")
            raise RAGServiceError(f"Embedding generation failed: {str(e)}")
    
    async def answer_question(self, request: QARequest) -> QAResponse:
        """
        Answer question using RAG with citations.
        
        Implements US-4.1: HSA Rules Q&A requirements including:
        - Natural language question processing
        - AI-powered answers based on knowledge base
        - Citations and sources for answers
        - Confidence level for responses
        
        Args:
            request: Q&A request with question and optional context
            
        Returns:
            QAResponse: Answer with citations and confidence score
        """
        start_time = datetime.utcnow()
        
        try:
            # Create question embedding for similarity search
            question_embedding = await self._create_embedding(request.question)
            
            # Search for relevant passages
            search_results = await self.vector_store.similarity_search(
                question_embedding,
                k=5,
                threshold=0.7
            )
            
            if not search_results:
                return QAResponse(
                    answer="I don't have information about that in my HSA knowledge base. Please rephrase your question or ask about HSA eligibility, contribution limits, qualified expenses, or account management.",
                    confidence_score=0.0,
                    citations=[],
                    source_documents=[],
                    processing_time_ms=self._calculate_processing_time(start_time)
                )
            
            # Prepare context and generate response
            context_chunks = []
            citations = []
            source_documents = set()
            
            for chunk_id, similarity_score in search_results:
                metadata = self.vector_store.get_metadata(chunk_id)
                if metadata:
                    context_chunks.append(metadata)
                    source_documents.add(metadata['document'])
                    
                    # Create citation
                    citation = Citation(
                        document_name=metadata['document'],
                        excerpt=self._create_excerpt(metadata['text'], request.question),
                        relevance_score=similarity_score
                    )
                    citations.append(citation)
            
            # Generate response using GPT-4o-mini
            response_text = await self._generate_response(request.question, context_chunks, request.context)
            confidence_score = self._calculate_confidence(search_results, response_text)
            
            # Update performance metrics
            processing_time = self._calculate_processing_time(start_time)
            self._update_metrics(confidence_score, processing_time)
            
            return QAResponse(
                answer=response_text,
                confidence_score=confidence_score,
                citations=citations,
                source_documents=list(source_documents),
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Failed to answer question: {str(e)}")
            raise RAGServiceError(f"Question answering failed: {str(e)}")
    
    async def _generate_response(
        self, 
        question: str, 
        context_chunks: List[Dict[str, Any]], 
        user_context: Optional[str] = None
    ) -> str:
        """Generate response using GPT-4o-mini with context."""
        
        # Prepare context for LLM
        context_text = "\n\n---\n\n".join([
            f"Source: {chunk['document']}\nContent: {chunk['text']}"
            for chunk in context_chunks
        ])
        
        # Create system prompt with instructions for citations
        system_prompt = """You are an expert HSA (Health Savings Account) advisor. Answer questions based ONLY on the provided context from official HSA documentation. 

IMPORTANT REQUIREMENTS:
1. Base your answer exclusively on the provided context
2. Include specific citations in your response by referencing the source documents
3. If the context doesn't contain sufficient information to answer the question, clearly state this
4. Provide accurate, helpful information about HSA rules, limits, and eligibility
5. Use clear, professional language appropriate for applicants and administrators
6. When mentioning specific numbers, dates, or limits, cite the source document

Format your response to be informative and well-structured with proper citations."""
        
        user_prompt = f"""Context from HSA documentation:
{context_text}

{f"Additional context: {user_context}" if user_context else ""}

Question: {question}

Please provide a comprehensive answer based on the context above, including proper citations to the source documents."""
        
        try:
            response = await self.openai_client.chat.completions.create(
                model=self.response_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Failed to generate response: {str(e)}")
            raise RAGServiceError(f"Response generation failed: {str(e)}")
    
    def _create_excerpt(self, text: str, question: str, max_length: int = 200) -> str:
        """Create relevant excerpt from text based on question."""
        # Simple implementation - find sentences containing key words from question
        question_words = set(question.lower().split())
        sentences = text.split('.')
        
        best_sentence = ""
        max_word_matches = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:  # Skip very short sentences
                continue
            
            sentence_words = set(sentence.lower().split())
            word_matches = len(question_words & sentence_words)
            
            if word_matches > max_word_matches:
                max_word_matches = word_matches
                best_sentence = sentence
        
        if best_sentence and len(best_sentence) <= max_length:
            return best_sentence + "."
        elif best_sentence:
            return best_sentence[:max_length-3] + "..."
        else:
            # Fallback to first part of text
            return text[:max_length-3] + "..." if len(text) > max_length else text
    
    def _calculate_confidence(self, search_results: List[Tuple[str, float]], response: str) -> float:
        """Calculate confidence score based on search results and response quality."""
        if not search_results:
            return 0.0
        
        # Base confidence on average similarity score of top results
        avg_similarity = sum(score for _, score in search_results) / len(search_results)
        
        # Adjust based on number of good matches
        result_quality = min(len(search_results) / 3, 1.0)  # Prefer 3+ results
        
        # Adjust based on response length (too short = less confident)
        response_length_factor = min(len(response) / 200, 1.0)
        
        # Combine factors
        confidence = avg_similarity * 0.6 + result_quality * 0.2 + response_length_factor * 0.2
        return min(confidence, 1.0)
    
    def _calculate_processing_time(self, start_time: datetime) -> int:
        """Calculate processing time in milliseconds."""
        return int((datetime.utcnow() - start_time).total_seconds() * 1000)
    
    def _update_metrics(self, confidence_score: float, processing_time_ms: int):
        """Update performance tracking metrics."""
        self.query_count += 1
        self.total_response_time += processing_time_ms
        self.confidence_scores.append(confidence_score)
    
    async def vector_search(self, request: VectorSearchRequest) -> List[VectorSearchResult]:
        """Perform vector similarity search on knowledge base."""
        try:
            query_embedding = await self._create_embedding(request.query)
            search_results = await self.vector_store.similarity_search(
                query_embedding,
                k=request.k,
                threshold=request.threshold
            )
            
            results = []
            for chunk_id, similarity_score in search_results:
                metadata = self.vector_store.get_metadata(chunk_id)
                if metadata:
                    # Apply document filter if specified
                    if request.filter_documents and metadata['document'] not in request.filter_documents:
                        continue
                    
                    result = VectorSearchResult(
                        chunk_id=chunk_id,
                        document_name=metadata['document'],
                        text=metadata['text'],
                        similarity_score=similarity_score,
                        metadata=metadata
                    )
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Vector search failed: {str(e)}")
            raise RAGServiceError(f"Vector search failed: {str(e)}")
    
    async def get_knowledge_base_stats(self) -> KnowledgeBaseStats:
        """Get statistics about the knowledge base."""
        try:
            total_documents = len(self.knowledge_base_index)
            total_chunks = self.vector_store.get_chunk_count()
            total_embeddings = len(self.vector_store.embeddings)
            
            # Calculate average chunk size
            if total_chunks > 0:
                total_chars = sum(
                    metadata.get('char_count', 0) 
                    for metadata in self.vector_store.metadata.values()
                )
                average_chunk_size = total_chars / total_chunks
            else:
                average_chunk_size = 0.0
            
            return KnowledgeBaseStats(
                total_documents=total_documents,
                total_chunks=total_chunks,
                total_embeddings=total_embeddings,
                average_chunk_size=average_chunk_size,
                last_index_update=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Failed to get knowledge base stats: {str(e)}")
            raise RAGServiceError(f"Stats calculation failed: {str(e)}")
    
    async def get_rag_metrics(self) -> RAGMetrics:
        """Get RAG system performance metrics."""
        try:
            avg_response_time = (
                self.total_response_time / self.query_count 
                if self.query_count > 0 else 0.0
            )
            
            avg_confidence = (
                sum(self.confidence_scores) / len(self.confidence_scores)
                if self.confidence_scores else 0.0
            )
            
            # Simple citation rate calculation (assume citations if confidence > 0.5)
            citation_rate = (
                len([c for c in self.confidence_scores if c > 0.5]) / len(self.confidence_scores)
                if self.confidence_scores else 0.0
            )
            
            return RAGMetrics(
                total_queries=self.query_count,
                average_response_time_ms=avg_response_time,
                average_confidence_score=avg_confidence,
                citation_rate=citation_rate,
                knowledge_coverage=0.5,  # Placeholder - would need more sophisticated tracking
                last_updated=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Failed to get RAG metrics: {str(e)}")
            raise RAGServiceError(f"Metrics calculation failed: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for RAG service."""
        return {
            "status": "healthy",
            "knowledge_base_loaded": len(self.knowledge_base_index) > 0,
            "total_documents": len(self.knowledge_base_index),
            "total_chunks": self.vector_store.get_chunk_count(),
            "queries_processed": self.query_count,
            "openai_client_configured": self.openai_client.api_key is not None
        }