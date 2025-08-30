"""
HSA Assistant API endpoints for HSA knowledge base queries.

This module provides REST API endpoints for the RAG-powered HSA Assistant system,
enabling natural language questions about HSA rules with cited responses.

Implements user stories US-4.1 and US-4.2 requirements.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Depends
from sqlalchemy.orm import Session
import logging

from ...core.database import get_db
from ...schemas.hsa_assistant import (
    QARequest, QAResponse, QAHistoryItem, VectorSearchRequest, VectorSearchResult,
    KnowledgeBaseStats, RAGMetrics
)
from ...services.rag_service import RAGService, RAGServiceError
from ...models.hsa_assistant_history import HSAAssistantHistory

# Initialize router and service
router = APIRouter(prefix="/hsa_assistant", tags=["hsa_assistant"])
logger = logging.getLogger(__name__)

# Global RAG service instance (in production, this would be dependency-injected)
_rag_service: Optional[RAGService] = None


async def get_rag_service() -> RAGService:
    """
    Dependency to get RAG service instance.
    
    Ensures knowledge base is built on first access.
    """
    global _rag_service
    
    if _rag_service is None:
        _rag_service = RAGService()
        try:
            await _rag_service.build_knowledge_base()
            logger.info("Knowledge base initialized successfully")
        except RAGServiceError as e:
            logger.error(f"Failed to initialize knowledge base: {str(e)}")
            # Continue with empty knowledge base for now
    
    return _rag_service


@router.post("/ask", response_model=QAResponse)
async def ask_question(
    request: QARequest,
    rag_service: RAGService = Depends(get_rag_service),
    db: Session = Depends(get_db)
) -> QAResponse:
    """
    Ask a question about HSA rules and regulations.
    
    This endpoint implements US-4.1 requirements:
    - Natural language question input
    - AI-powered answers based on HSA knowledge base
    - Provide citations and sources for answers
    - Show confidence level for responses
    - Handle follow-up questions with context
    
    Args:
        request: Question request with optional context
        rag_service: RAG service dependency
        db: Database session dependency
        
    Returns:
        QAResponse: Answer with citations and confidence score
        
    Raises:
        HTTPException: If question processing fails
    """
    try:
        logger.info(f"Processing question: {request.question[:100]}...")
        
        # Generate response using RAG service
        response = await rag_service.answer_question(request)
        
        # Store HSA Assistant session in database for history tracking
        assistant_record = HSAAssistantHistory(
            question=request.question,
            answer=response.answer,
            confidence_score=response.confidence_score,
            citations_count=len(response.citations),
            processing_time_ms=response.processing_time_ms,
            application_id=request.application_id,
            context=request.context,
            source_documents=",".join(response.source_documents)
        )
        db.add(assistant_record)
        db.commit()
        logger.info(f"Stored HSA Assistant history record with ID: {assistant_record.id}")
        
        logger.info(f"Question answered with confidence {response.confidence_score:.2f}")
        return response
        
    except RAGServiceError as e:
        logger.error(f"RAG service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Question processing failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in question processing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your question"
        )


@router.get("/history/{application_id}", response_model=List[QAHistoryItem])
async def get_hsa_assistant_history(
    application_id: str,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
) -> List[QAHistoryItem]:
    """
    Get HSA Assistant history for a specific application.
    
    Args:
        application_id: Application ID to get history for
        limit: Maximum number of items to return (default 50)
        offset: Number of items to skip (default 0)
        db: Database session dependency
        
    Returns:
        List[QAHistoryItem]: Historical HSA Assistant interactions
        
    Raises:
        HTTPException: If application not found or retrieval fails
    """
    try:
        # Query HSA Assistant history from database
        query = db.query(HSAAssistantHistory)
        if application_id and application_id != "all":
            query = query.filter(HSAAssistantHistory.application_id == application_id)
        
        history_records = query.order_by(HSAAssistantHistory.created_at.desc()).offset(offset).limit(limit).all()
        
        # Convert to response format
        history_items = [
            QAHistoryItem(
                id=str(record.id),
                question=record.question,
                answer=record.answer,
                confidence_score=record.confidence_score,
                citations_count=record.citations_count,
                application_id=record.application_id,
                created_at=record.created_at
            )
            for record in history_records
        ]
        
        logger.info(f"Retrieved {len(history_items)} HSA Assistant history items for application {application_id}")
        return history_items
        
    except Exception as e:
        logger.error(f"Failed to retrieve HSA Assistant history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve HSA Assistant history"
        )


@router.post("/search", response_model=List[VectorSearchResult])
async def vector_search(
    request: VectorSearchRequest,
    rag_service: RAGService = Depends(get_rag_service)
) -> List[VectorSearchResult]:
    """
    Perform vector similarity search on knowledge base.
    
    This endpoint allows direct access to the vector search functionality
    for debugging and advanced users.
    
    Args:
        request: Vector search parameters
        rag_service: RAG service dependency
        
    Returns:
        List[VectorSearchResult]: Similar document chunks
        
    Raises:
        HTTPException: If search fails
    """
    try:
        logger.info(f"Performing vector search: {request.query[:100]}...")
        
        results = await rag_service.vector_search(request)
        
        logger.info(f"Vector search returned {len(results)} results")
        return results
        
    except RAGServiceError as e:
        logger.error(f"Vector search error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vector search failed: {str(e)}"
        )


@router.get("/stats", response_model=KnowledgeBaseStats)
async def get_knowledge_base_stats(
    rag_service: RAGService = Depends(get_rag_service)
) -> KnowledgeBaseStats:
    """
    Get statistics about the knowledge base.
    
    Useful for monitoring and debugging the RAG system.
    
    Args:
        rag_service: RAG service dependency
        
    Returns:
        KnowledgeBaseStats: Knowledge base statistics
        
    Raises:
        HTTPException: If stats calculation fails
    """
    try:
        stats = await rag_service.get_knowledge_base_stats()
        logger.info(f"Retrieved knowledge base stats: {stats.total_documents} documents")
        return stats
        
    except RAGServiceError as e:
        logger.error(f"Failed to get knowledge base stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve knowledge base statistics"
        )


@router.get("/metrics", response_model=RAGMetrics)
async def get_rag_metrics(
    rag_service: RAGService = Depends(get_rag_service)
) -> RAGMetrics:
    """
    Get RAG system performance metrics.
    
    Provides insights into system performance, citation rates, and usage patterns.
    
    Args:
        rag_service: RAG service dependency
        
    Returns:
        RAGMetrics: RAG system performance metrics
        
    Raises:
        HTTPException: If metrics calculation fails
    """
    try:
        metrics = await rag_service.get_rag_metrics()
        logger.info(f"Retrieved RAG metrics: {metrics.total_queries} queries processed")
        return metrics
        
    except RAGServiceError as e:
        logger.error(f"Failed to get RAG metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve RAG metrics"
        )


@router.post("/rebuild", status_code=202)
async def rebuild_knowledge_base(
    background_tasks: BackgroundTasks,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Trigger knowledge base rebuild.
    
    Implements US-4.2 requirement for knowledge base management.
    This endpoint rebuilds the vector embeddings from source documents.
    
    Args:
        background_tasks: FastAPI background tasks for async processing
        rag_service: RAG service dependency
        
    Returns:
        Success message
        
    Note:
        In production, this endpoint should be protected with admin authentication.
    """
    try:
        # Add rebuild task to background queue
        background_tasks.add_task(_rebuild_knowledge_base_task, rag_service)
        
        logger.info("Knowledge base rebuild task scheduled")
        return {"message": "Knowledge base rebuild started. This may take several minutes."}
        
    except Exception as e:
        logger.error(f"Failed to schedule knowledge base rebuild: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to schedule knowledge base rebuild"
        )


async def _rebuild_knowledge_base_task(rag_service: RAGService):
    """Background task to rebuild knowledge base."""
    try:
        logger.info("Starting knowledge base rebuild...")
        await rag_service.build_knowledge_base()
        logger.info("Knowledge base rebuild completed successfully")
        
    except Exception as e:
        logger.error(f"Knowledge base rebuild failed: {str(e)}")


@router.get("/health")
async def hsa_assistant_health_check(
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Health check for HSA Assistant service.
    
    Returns:
        Health status and service information
    """
    try:
        health_info = await rag_service.health_check()
        health_info["service"] = "hsa_assistant"
        health_info["timestamp"] = "2024-01-01T00:00:00Z"  # Would use actual timestamp
        
        return health_info
        
    except Exception as e:
        logger.error(f"HSA Assistant health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="HSA Assistant service is unhealthy"
        )


# Example questions for API documentation
EXAMPLE_QUESTIONS = [
    "What are the HSA contribution limits for 2024?",
    "Am I eligible for an HSA if I have other health insurance?",
    "Can I use my HSA for dental expenses?",
    "What happens to my HSA when I turn 65?",
    "Do HSA funds expire at the end of the year?",
    "Can I contribute to an HSA if I'm self-employed?",
    "What documentation do I need to keep for HSA expenses?",
    "Are there penalties for non-qualified HSA withdrawals?",
    "Can I invest my HSA funds?",
    "What qualifies as a high-deductible health plan?"
]


@router.get("/examples")
async def get_example_questions():
    """
    Get example questions for testing and documentation.
    
    Returns:
        List of example questions users can ask
    """
    return {"example_questions": EXAMPLE_QUESTIONS}