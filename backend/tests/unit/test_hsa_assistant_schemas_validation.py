"""
Unit tests for HSA Assistant schema validation.

Tests the Pydantic schema validation for the OpenAI Vector Stores
implementation without requiring external API dependencies.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from backend.schemas.hsa_assistant import (
    QARequest, QAResponse, Citation, VectorSearchRequest, VectorSearchResult,
    KnowledgeBaseStats, RAGMetrics, QAHistoryItem
)


class TestQARequestValidation:
    """Test QA request schema validation."""

    def test_valid_qa_request(self):
        """Test valid QA request creation."""
        request = QARequest(
            question="What are the HSA contribution limits for 2024?",
            context="I need information for self-only coverage",
            application_id="app-123"
        )
        
        assert request.question == "What are the HSA contribution limits for 2024?"
        assert request.context == "I need information for self-only coverage"
        assert request.application_id == "app-123"

    def test_qa_request_minimal(self):
        """Test QA request with only required fields."""
        request = QARequest(question="What are HSA limits?")
        
        assert request.question == "What are HSA limits?"
        assert request.context is None
        assert request.application_id is None

    def test_qa_request_question_too_short(self):
        """Test QA request validation with question too short."""
        with pytest.raises(ValidationError) as exc_info:
            QARequest(question="Hi")
        
        assert "at least 10 characters" in str(exc_info.value)

    def test_qa_request_question_too_long(self):
        """Test QA request validation with question too long."""
        long_question = "A" * 501  # Exceeds 500 char limit
        
        with pytest.raises(ValidationError) as exc_info:
            QARequest(question=long_question)
        
        assert "at most 500 characters" in str(exc_info.value)

    def test_qa_request_context_too_long(self):
        """Test QA request validation with context too long."""
        long_context = "B" * 1001  # Exceeds 1000 char limit
        
        with pytest.raises(ValidationError) as exc_info:
            QARequest(question="Valid question here", context=long_context)
        
        assert "at most 1000 characters" in str(exc_info.value)


class TestQAResponseValidation:
    """Test QA response schema validation."""

    def test_valid_qa_response(self):
        """Test valid QA response creation."""
        response = QAResponse(
            answer="HSA contribution limits for 2024 are $4,150 for individual coverage.",
            confidence_score=0.85,
            citations=[
                Citation(
                    document_name="irs.pdf",
                    excerpt="2024 limits are $4,150 for self-only",
                    relevance_score=0.9
                )
            ],
            source_documents=["irs.pdf"],
            processing_time_ms=1200
        )
        
        assert response.answer == "HSA contribution limits for 2024 are $4,150 for individual coverage."
        assert response.confidence_score == 0.85
        assert len(response.citations) == 1
        assert response.source_documents == ["irs.pdf"]
        assert response.processing_time_ms == 1200
        assert isinstance(response.created_at, datetime)

    def test_qa_response_confidence_score_bounds(self):
        """Test QA response confidence score validation."""
        # Valid confidence scores
        response = QAResponse(
            answer="Test answer",
            confidence_score=0.0,
            citations=[],
            source_documents=[]
        )
        assert response.confidence_score == 0.0
        
        response = QAResponse(
            answer="Test answer", 
            confidence_score=1.0,
            citations=[],
            source_documents=[]
        )
        assert response.confidence_score == 1.0
        
        # Invalid confidence scores
        with pytest.raises(ValidationError):
            QAResponse(
                answer="Test answer",
                confidence_score=-0.1,  # Below 0.0
                citations=[],
                source_documents=[]
            )
        
        with pytest.raises(ValidationError):
            QAResponse(
                answer="Test answer",
                confidence_score=1.1,  # Above 1.0
                citations=[],
                source_documents=[]
            )

    def test_qa_response_citations_limit(self):
        """Test QA response citations list size limit."""
        # Create 11 citations (exceeds max 10)
        citations = [
            Citation(document_name="irs.pdf", excerpt=f"Excerpt {i}", relevance_score=0.8)
            for i in range(11)
        ]
        
        with pytest.raises(ValidationError) as exc_info:
            QAResponse(
                answer="Test answer",
                confidence_score=0.8,
                citations=citations,
                source_documents=["irs.pdf"]
            )
        
        assert "at most 10 items" in str(exc_info.value)


class TestCitationValidation:
    """Test Citation schema validation."""

    def test_valid_citation(self):
        """Test valid citation creation."""
        citation = Citation(
            document_name="irs.pdf",
            page_number=5,
            excerpt="HSA contribution limits are specified in this section.",
            relevance_score=0.92
        )
        
        assert citation.document_name == "irs.pdf"
        assert citation.page_number == 5
        assert citation.excerpt == "HSA contribution limits are specified in this section."
        assert citation.relevance_score == 0.92

    def test_citation_optional_page_number(self):
        """Test citation with optional page number."""
        citation = Citation(
            document_name="irs.pdf",
            excerpt="Test excerpt",
            relevance_score=0.8
        )
        
        assert citation.page_number is None

    def test_citation_excerpt_length_limit(self):
        """Test citation excerpt length validation."""
        long_excerpt = "A" * 501  # Exceeds 500 char limit
        
        with pytest.raises(ValidationError) as exc_info:
            Citation(
                document_name="irs.pdf",
                excerpt=long_excerpt,
                relevance_score=0.8
            )
        
        assert "at most 500 characters" in str(exc_info.value)

    def test_citation_relevance_score_bounds(self):
        """Test citation relevance score validation."""
        # Valid scores
        citation = Citation(document_name="irs.pdf", excerpt="Test", relevance_score=0.0)
        assert citation.relevance_score == 0.0
        
        citation = Citation(document_name="irs.pdf", excerpt="Test", relevance_score=1.0)
        assert citation.relevance_score == 1.0
        
        # Invalid scores
        with pytest.raises(ValidationError):
            Citation(document_name="irs.pdf", excerpt="Test", relevance_score=-0.1)
        
        with pytest.raises(ValidationError):
            Citation(document_name="irs.pdf", excerpt="Test", relevance_score=1.1)


class TestVectorSearchRequestValidation:
    """Test Vector Search request schema validation."""

    def test_valid_vector_search_request(self):
        """Test valid vector search request creation."""
        request = VectorSearchRequest(
            query="HSA contribution limits",
            k=5,
            threshold=0.7,
            filter_documents=["irs.pdf"]
        )
        
        assert request.query == "HSA contribution limits"
        assert request.k == 5
        assert request.threshold == 0.7
        assert request.filter_documents == ["irs.pdf"]

    def test_vector_search_request_defaults(self):
        """Test vector search request with default values."""
        request = VectorSearchRequest(query="HSA eligibility")
        
        assert request.query == "HSA eligibility"
        assert request.k == 5  # Default
        assert request.threshold == 0.7  # Default
        assert request.filter_documents is None

    def test_vector_search_query_length_validation(self):
        """Test vector search query length validation."""
        # Too short
        with pytest.raises(ValidationError):
            VectorSearchRequest(query="Hi")
        
        # Too long
        long_query = "A" * 501
        with pytest.raises(ValidationError):
            VectorSearchRequest(query=long_query)

    def test_vector_search_k_validation(self):
        """Test vector search k parameter validation."""
        # Valid k values
        request = VectorSearchRequest(query="HSA limits", k=1)
        assert request.k == 1
        
        request = VectorSearchRequest(query="HSA limits", k=20)
        assert request.k == 20
        
        # Invalid k values
        with pytest.raises(ValidationError):
            VectorSearchRequest(query="HSA limits", k=0)
        
        with pytest.raises(ValidationError):
            VectorSearchRequest(query="HSA limits", k=21)

    def test_vector_search_threshold_validation(self):
        """Test vector search threshold parameter validation."""
        # Valid threshold values
        request = VectorSearchRequest(query="HSA limits", threshold=0.0)
        assert request.threshold == 0.0
        
        request = VectorSearchRequest(query="HSA limits", threshold=1.0)
        assert request.threshold == 1.0
        
        # Invalid threshold values
        with pytest.raises(ValidationError):
            VectorSearchRequest(query="HSA limits", threshold=-0.1)
        
        with pytest.raises(ValidationError):
            VectorSearchRequest(query="HSA limits", threshold=1.1)


class TestVectorSearchResultValidation:
    """Test Vector Search result schema validation."""

    def test_valid_vector_search_result(self):
        """Test valid vector search result creation."""
        result = VectorSearchResult(
            chunk_id="chunk_1",
            document_name="irs.pdf",
            text="HSA contribution limits for 2024 are $4,150",
            similarity_score=0.95,
            metadata={"chunk_index": 0, "document": "irs.pdf"}
        )
        
        assert result.chunk_id == "chunk_1"
        assert result.document_name == "irs.pdf"
        assert result.text == "HSA contribution limits for 2024 are $4,150"
        assert result.similarity_score == 0.95
        assert result.metadata == {"chunk_index": 0, "document": "irs.pdf"}

    def test_vector_search_result_empty_metadata(self):
        """Test vector search result with empty metadata."""
        result = VectorSearchResult(
            chunk_id="chunk_1",
            document_name="irs.pdf",
            text="Test text",
            similarity_score=0.8
        )
        
        assert result.metadata == {}

    def test_vector_search_result_similarity_score_bounds(self):
        """Test vector search result similarity score validation."""
        # Valid scores
        result = VectorSearchResult(
            chunk_id="chunk_1", document_name="irs.pdf", 
            text="Test", similarity_score=0.0
        )
        assert result.similarity_score == 0.0
        
        result = VectorSearchResult(
            chunk_id="chunk_1", document_name="irs.pdf",
            text="Test", similarity_score=1.0
        )
        assert result.similarity_score == 1.0
        
        # Invalid scores
        with pytest.raises(ValidationError):
            VectorSearchResult(
                chunk_id="chunk_1", document_name="irs.pdf",
                text="Test", similarity_score=-0.1
            )
        
        with pytest.raises(ValidationError):
            VectorSearchResult(
                chunk_id="chunk_1", document_name="irs.pdf",
                text="Test", similarity_score=1.1
            )


class TestKnowledgeBaseStatsValidation:
    """Test Knowledge Base stats schema validation."""

    def test_valid_knowledge_base_stats(self):
        """Test valid knowledge base stats creation."""
        stats = KnowledgeBaseStats(
            total_documents=5,
            total_chunks=50,
            total_embeddings=50,
            average_chunk_size=1000.5,
            last_index_update=datetime.utcnow()
        )
        
        assert stats.total_documents == 5
        assert stats.total_chunks == 50
        assert stats.total_embeddings == 50
        assert stats.average_chunk_size == 1000.5
        assert isinstance(stats.last_index_update, datetime)

    def test_knowledge_base_stats_non_negative_values(self):
        """Test knowledge base stats validation for non-negative values."""
        now = datetime.utcnow()
        
        # Valid zero values
        stats = KnowledgeBaseStats(
            total_documents=0,
            total_chunks=0,
            total_embeddings=0,
            average_chunk_size=0.0,
            last_index_update=now
        )
        assert stats.total_documents == 0
        
        # Invalid negative values
        with pytest.raises(ValidationError):
            KnowledgeBaseStats(
                total_documents=-1,
                total_chunks=0,
                total_embeddings=0,
                average_chunk_size=0.0,
                last_index_update=now
            )


class TestRAGMetricsValidation:
    """Test RAG metrics schema validation."""

    def test_valid_rag_metrics(self):
        """Test valid RAG metrics creation."""
        metrics = RAGMetrics(
            total_queries=100,
            average_response_time_ms=850.5,
            average_confidence_score=0.82,
            citation_rate=0.88,
            knowledge_coverage=0.95
        )
        
        assert metrics.total_queries == 100
        assert metrics.average_response_time_ms == 850.5
        assert metrics.average_confidence_score == 0.82
        assert metrics.citation_rate == 0.88
        assert metrics.knowledge_coverage == 0.95
        assert isinstance(metrics.last_updated, datetime)

    def test_rag_metrics_bounds_validation(self):
        """Test RAG metrics bounds validation."""
        # Valid boundary values
        metrics = RAGMetrics(
            total_queries=0,
            average_response_time_ms=0.0,
            average_confidence_score=0.0,
            citation_rate=0.0,
            knowledge_coverage=0.0
        )
        assert metrics.total_queries == 0
        
        metrics = RAGMetrics(
            total_queries=1000,
            average_response_time_ms=5000.0,
            average_confidence_score=1.0,
            citation_rate=1.0,
            knowledge_coverage=1.0
        )
        assert metrics.average_confidence_score == 1.0
        
        # Invalid values
        with pytest.raises(ValidationError):
            RAGMetrics(
                total_queries=-1,  # Negative
                average_response_time_ms=0.0,
                average_confidence_score=0.5,
                citation_rate=0.5,
                knowledge_coverage=0.5
            )
        
        with pytest.raises(ValidationError):
            RAGMetrics(
                total_queries=100,
                average_response_time_ms=0.0,
                average_confidence_score=1.1,  # > 1.0
                citation_rate=0.5,
                knowledge_coverage=0.5
            )


class TestQAHistoryItemValidation:
    """Test QA history item schema validation."""

    def test_valid_qa_history_item(self):
        """Test valid QA history item creation."""
        item = QAHistoryItem(
            id="hist_123",
            question="What are HSA limits?",
            answer="HSA limits for 2024 are $4,150 for individual coverage.",
            confidence_score=0.85,
            citations_count=2,
            application_id="app_456",
            created_at=datetime.utcnow()
        )
        
        assert item.id == "hist_123"
        assert item.question == "What are HSA limits?"
        assert item.answer == "HSA limits for 2024 are $4,150 for individual coverage."
        assert item.confidence_score == 0.85
        assert item.citations_count == 2
        assert item.application_id == "app_456"
        assert isinstance(item.created_at, datetime)

    def test_qa_history_item_optional_application_id(self):
        """Test QA history item with optional application ID."""
        item = QAHistoryItem(
            id="hist_123",
            question="Test question",
            answer="Test answer",
            confidence_score=0.7,
            citations_count=1,
            created_at=datetime.utcnow()
        )
        
        assert item.application_id is None

    def test_qa_history_item_citations_count_non_negative(self):
        """Test QA history item citations count validation."""
        # Valid counts
        item = QAHistoryItem(
            id="hist_123", question="Test", answer="Test",
            confidence_score=0.7, citations_count=0,
            created_at=datetime.utcnow()
        )
        assert item.citations_count == 0
        
        # Invalid negative count
        with pytest.raises(ValidationError):
            QAHistoryItem(
                id="hist_123", question="Test", answer="Test",
                confidence_score=0.7, citations_count=-1,
                created_at=datetime.utcnow()
            )