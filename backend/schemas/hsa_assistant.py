"""
HSA Assistant system schemas for HSA knowledge base queries.

This module defines Pydantic models for the RAG-powered HSA Assistant system,
providing validation, serialization, and documentation for HSA Assistant APIs.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class Citation(BaseModel):
    """Citation reference from knowledge base."""
    
    document_name: str = Field(
        ...,
        description="Name of the source document",
        example="HSA_FAQ.txt"
    )
    
    page_number: Optional[int] = Field(
        None,
        description="Page number within the document (if applicable)",
        example=1
    )
    
    excerpt: str = Field(
        ...,
        max_length=500,
        description="Relevant excerpt from the source document",
        example="To be eligible for an HSA, you must be covered under a high-deductible health plan..."
    )
    
    relevance_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Relevance score for this citation (0.0 = not relevant, 1.0 = highly relevant)",
        example=0.92
    )


class QARequest(BaseModel):
    """Request schema for asking questions about HSA rules."""
    
    question: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="The question about HSA rules and eligibility",
        example="What are the contribution limits for HSA in 2024?"
    )
    
    context: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional context for follow-up questions",
        example="I'm asking about self-only coverage"
    )
    
    application_id: Optional[str] = Field(
        None,
        description="Application ID for tracking Q&A history",
        example="app-12345"
    )


class QAResponse(BaseModel):
    """Response schema for HSA Q&A answers."""
    
    answer: str = Field(
        ...,
        description="AI-generated answer based on HSA knowledge base",
        example="For 2024, the HSA contribution limits are $4,150 for self-only coverage and $8,300 for family coverage."
    )
    
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for the answer quality (0.0 = low confidence, 1.0 = high confidence)",
        example=0.95
    )
    
    citations: List[Citation] = Field(
        default_factory=list,
        description="List of citations supporting the answer",
        max_length=10
    )
    
    source_documents: List[str] = Field(
        default_factory=list,
        description="List of source document names used",
        example=["HSA_FAQ.txt", "HSA_Limits.txt"]
    )
    
    processing_time_ms: Optional[int] = Field(
        None,
        description="Time taken to process the question in milliseconds",
        example=1250
    )
    
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the response was generated"
    )


class QAHistoryItem(BaseModel):
    """Q&A session history item."""
    
    id: str = Field(
        ...,
        description="Unique identifier for this Q&A interaction"
    )
    
    question: str = Field(
        ...,
        description="The question that was asked"
    )
    
    answer: str = Field(
        ...,
        description="The answer that was provided"
    )
    
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for the answer"
    )
    
    citations_count: int = Field(
        ...,
        ge=0,
        description="Number of citations provided with the answer"
    )
    
    application_id: Optional[str] = Field(
        None,
        description="Associated application ID"
    )
    
    created_at: datetime = Field(
        ...,
        description="When the question was asked"
    )


class KnowledgeBaseDocument(BaseModel):
    """Knowledge base document metadata."""
    
    id: str = Field(
        ...,
        description="Unique document identifier"
    )
    
    name: str = Field(
        ...,
        description="Document name/filename"
    )
    
    title: str = Field(
        ...,
        description="Human-readable document title"
    )
    
    description: Optional[str] = Field(
        None,
        description="Document description"
    )
    
    content_length: int = Field(
        ...,
        ge=0,
        description="Length of document content in characters"
    )
    
    chunk_count: int = Field(
        ...,
        ge=0,
        description="Number of chunks this document was split into"
    )
    
    last_updated: datetime = Field(
        ...,
        description="When the document was last updated"
    )
    
    created_at: datetime = Field(
        ...,
        description="When the document was added to the knowledge base"
    )


class KnowledgeBaseStats(BaseModel):
    """Knowledge base statistics."""
    
    total_documents: int = Field(
        ...,
        ge=0,
        description="Total number of documents in knowledge base"
    )
    
    total_chunks: int = Field(
        ...,
        ge=0,
        description="Total number of text chunks"
    )
    
    total_embeddings: int = Field(
        ...,
        ge=0,
        description="Total number of vector embeddings"
    )
    
    average_chunk_size: float = Field(
        ...,
        ge=0.0,
        description="Average chunk size in characters"
    )
    
    last_index_update: datetime = Field(
        ...,
        description="When the index was last updated"
    )


class VectorSearchRequest(BaseModel):
    """Request for vector similarity search."""
    
    query: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Search query text"
    )
    
    k: int = Field(
        5,
        ge=1,
        le=20,
        description="Number of similar documents to retrieve"
    )
    
    threshold: float = Field(
        0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score threshold"
    )
    
    filter_documents: Optional[List[str]] = Field(
        None,
        description="Optional list of document names to filter by"
    )


class VectorSearchResult(BaseModel):
    """Vector similarity search result."""
    
    chunk_id: str = Field(
        ...,
        description="Unique identifier for the text chunk"
    )
    
    document_name: str = Field(
        ...,
        description="Source document name"
    )
    
    text: str = Field(
        ...,
        description="The matching text chunk"
    )
    
    similarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Similarity score with the query"
    )
    
    metadata: dict = Field(
        default_factory=dict,
        description="Additional metadata about the chunk"
    )


class RAGMetrics(BaseModel):
    """RAG system performance metrics."""
    
    total_queries: int = Field(
        ...,
        ge=0,
        description="Total number of queries processed"
    )
    
    average_response_time_ms: float = Field(
        ...,
        ge=0.0,
        description="Average response time in milliseconds"
    )
    
    average_confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Average confidence score across all responses"
    )
    
    citation_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Percentage of responses that included citations"
    )
    
    knowledge_coverage: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Percentage of knowledge base accessed by queries"
    )
    
    last_updated: datetime = Field(
        default_factory=datetime.utcnow,
        description="When these metrics were last calculated"
    )