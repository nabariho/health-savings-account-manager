"""
Integration tests for Q&A API endpoints.

Tests the complete RAG Q&A workflow including API endpoints, RAG service integration,
citation accuracy, and response quality as specified in user stories US-4.1 and US-4.2.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
import tempfile
import shutil
from pathlib import Path

from backend.main import app
from backend.schemas.qa import QAResponse, Citation, VectorSearchResult, KnowledgeBaseStats


@pytest.fixture
def client():
    """Test client for API endpoints."""
    return TestClient(app)


@pytest.fixture
def mock_knowledge_base():
    """Mock knowledge base setup for testing."""
    temp_dir = tempfile.mkdtemp()
    kb_path = Path(temp_dir) / "knowledge_base"
    kb_path.mkdir()
    
    # Create test knowledge base files
    (kb_path / "HSA_FAQ.txt").write_text(
        "# HSA FAQ\n\n"
        "What are HSA contribution limits for 2024?\n"
        "For 2024, HSA contribution limits are $4,150 for self-only coverage and $8,300 for family coverage.\n\n"
        "Who is eligible for an HSA?\n"
        "You must be covered under a high-deductible health plan and have no other health coverage."
    )
    
    yield str(kb_path)
    shutil.rmtree(temp_dir)


class TestQAAskEndpoint:
    """Test cases for /api/v1/qa/ask endpoint."""

    @patch('backend.api.v1.qa.get_rag_service')
    def test_ask_question_success(self, mock_get_rag_service, client):
        """Test successful question processing with citations."""
        # Mock RAG service
        mock_rag = AsyncMock()
        mock_response = QAResponse(
            answer="For 2024, HSA contribution limits are $4,150 for self-only coverage and $8,300 for family coverage, as specified in HSA_FAQ.txt.",
            confidence_score=0.92,
            citations=[
                Citation(
                    document_name="HSA_FAQ.txt",
                    excerpt="For 2024, HSA contribution limits are $4,150 for self-only coverage and $8,300 for family coverage.",
                    relevance_score=0.95
                )
            ],
            source_documents=["HSA_FAQ.txt"],
            processing_time_ms=1250
        )
        mock_rag.answer_question.return_value = mock_response
        mock_get_rag_service.return_value = mock_rag
        
        # Make request
        response = client.post(
            "/api/v1/qa/ask",
            json={
                "question": "What are the HSA contribution limits for 2024?",
                "application_id": "test-app-123"
            }
        )
        
        # Verify response
        assert response.status_code == 200
        result = response.json()
        
        # Verify required fields
        assert "answer" in result
        assert "confidence_score" in result
        assert "citations" in result
        assert "source_documents" in result
        assert "processing_time_ms" in result
        assert "created_at" in result
        
        # Verify content quality
        assert "4,150" in result["answer"] or "4150" in result["answer"]
        assert result["confidence_score"] > 0.8
        assert len(result["citations"]) > 0
        assert len(result["source_documents"]) > 0
        
        # Verify citation structure
        citation = result["citations"][0]
        assert "document_name" in citation
        assert "excerpt" in citation
        assert "relevance_score" in citation
        assert citation["document_name"] == "HSA_FAQ.txt"
        assert citation["relevance_score"] > 0.9

    @patch('backend.api.v1.qa.get_rag_service')
    def test_ask_question_with_context(self, mock_get_rag_service, client):
        """Test question processing with additional context."""
        # Mock RAG service
        mock_rag = AsyncMock()
        mock_response = QAResponse(
            answer="For self-only coverage in 2024, the HSA contribution limit is $4,150.",
            confidence_score=0.88,
            citations=[
                Citation(
                    document_name="HSA_FAQ.txt",
                    excerpt="$4,150 for self-only coverage",
                    relevance_score=0.90
                )
            ],
            source_documents=["HSA_FAQ.txt"],
            processing_time_ms=980
        )
        mock_rag.answer_question.return_value = mock_response
        mock_get_rag_service.return_value = mock_rag
        
        # Make request with context
        response = client.post(
            "/api/v1/qa/ask",
            json={
                "question": "What is the contribution limit?",
                "context": "I am asking about individual coverage",
                "application_id": "test-app-456"
            }
        )
        
        # Verify response
        assert response.status_code == 200
        result = response.json()
        assert "4,150" in result["answer"] or "4150" in result["answer"]
        assert result["confidence_score"] > 0.8

    @patch('backend.api.v1.qa.get_rag_service')
    def test_ask_question_no_answer_available(self, mock_get_rag_service, client):
        """Test handling when no relevant answer is found."""
        # Mock RAG service
        mock_rag = AsyncMock()
        mock_response = QAResponse(
            answer="I don't have information about that in my HSA knowledge base. Please rephrase your question or ask about HSA eligibility, contribution limits, qualified expenses, or account management.",
            confidence_score=0.0,
            citations=[],
            source_documents=[],
            processing_time_ms=500
        )
        mock_rag.answer_question.return_value = mock_response
        mock_get_rag_service.return_value = mock_rag
        
        # Make request with unrelated question
        response = client.post(
            "/api/v1/qa/ask",
            json={
                "question": "What is the capital of France?",
                "application_id": "test-app-789"
            }
        )
        
        # Verify response
        assert response.status_code == 200
        result = response.json()
        assert "don't have information" in result["answer"].lower()
        assert result["confidence_score"] == 0.0
        assert len(result["citations"]) == 0
        assert len(result["source_documents"]) == 0

    def test_ask_question_invalid_input(self, client):
        """Test validation of invalid question input."""
        # Test missing question
        response = client.post("/api/v1/qa/ask", json={})
        assert response.status_code == 422
        
        # Test question too short
        response = client.post("/api/v1/qa/ask", json={"question": "Hi"})
        assert response.status_code == 422
        
        # Test question too long
        long_question = "A" * 600  # Exceeds 500 char limit
        response = client.post("/api/v1/qa/ask", json={"question": long_question})
        assert response.status_code == 422
        
        # Test context too long
        response = client.post(
            "/api/v1/qa/ask", 
            json={
                "question": "What are HSA limits?",
                "context": "B" * 1100  # Exceeds 1000 char limit
            }
        )
        assert response.status_code == 422

    @patch('backend.api.v1.qa.get_rag_service')
    def test_ask_question_service_error(self, mock_get_rag_service, client):
        """Test handling of RAG service errors."""
        # Mock RAG service to raise error
        mock_rag = AsyncMock()
        mock_rag.answer_question.side_effect = Exception("RAG service error")
        mock_get_rag_service.return_value = mock_rag
        
        # Make request
        response = client.post(
            "/api/v1/qa/ask",
            json={"question": "What are HSA contribution limits?"}
        )
        
        # Verify error response
        assert response.status_code == 500
        assert "error occurred" in response.json()["detail"].lower()


class TestQAHistoryEndpoint:
    """Test cases for /api/v1/qa/history/{application_id} endpoint."""

    def test_get_qa_history_success(self, client):
        """Test successful retrieval of Q&A history."""
        # Currently returns empty list as database integration is not implemented
        response = client.get("/api/v1/qa/history/test-app-123")
        
        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)
        # Will be empty until database integration is added

    def test_get_qa_history_with_pagination(self, client):
        """Test Q&A history retrieval with pagination parameters."""
        response = client.get("/api/v1/qa/history/test-app-123?limit=10&offset=5")
        
        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)

    def test_get_qa_history_invalid_pagination(self, client):
        """Test Q&A history with invalid pagination parameters."""
        # Negative limit should be handled gracefully
        response = client.get("/api/v1/qa/history/test-app-123?limit=-5")
        assert response.status_code in [200, 422]  # Depends on validation implementation


class TestVectorSearchEndpoint:
    """Test cases for /api/v1/qa/search endpoint."""

    @patch('backend.api.v1.qa.get_rag_service')
    def test_vector_search_success(self, mock_get_rag_service, client):
        """Test successful vector similarity search."""
        # Mock RAG service
        mock_rag = AsyncMock()
        mock_results = [
            VectorSearchResult(
                chunk_id="chunk_1",
                document_name="HSA_FAQ.txt",
                text="HSA contribution limits for 2024 are $4,150 for self-only coverage",
                similarity_score=0.95,
                metadata={"chunk_index": 0}
            ),
            VectorSearchResult(
                chunk_id="chunk_2",
                document_name="HSA_Limits.txt",
                text="Family coverage maximum annual contribution is $8,300",
                similarity_score=0.87,
                metadata={"chunk_index": 1}
            )
        ]
        mock_rag.vector_search.return_value = mock_results
        mock_get_rag_service.return_value = mock_rag
        
        # Make request
        response = client.post(
            "/api/v1/qa/search",
            json={
                "query": "HSA contribution limits",
                "k": 5,
                "threshold": 0.7
            }
        )
        
        # Verify response
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 2
        
        # Verify result structure
        first_result = result[0]
        assert "chunk_id" in first_result
        assert "document_name" in first_result
        assert "text" in first_result
        assert "similarity_score" in first_result
        assert "metadata" in first_result
        
        # Verify similarity scores are in descending order
        assert result[0]["similarity_score"] >= result[1]["similarity_score"]

    @patch('backend.api.v1.qa.get_rag_service')
    def test_vector_search_with_filters(self, mock_get_rag_service, client):
        """Test vector search with document filters."""
        mock_rag = AsyncMock()
        mock_results = [
            VectorSearchResult(
                chunk_id="chunk_1",
                document_name="HSA_FAQ.txt",
                text="HSA eligibility requirements",
                similarity_score=0.92,
                metadata={}
            )
        ]
        mock_rag.vector_search.return_value = mock_results
        mock_get_rag_service.return_value = mock_rag
        
        # Make request with document filter
        response = client.post(
            "/api/v1/qa/search",
            json={
                "query": "HSA eligibility",
                "k": 3,
                "threshold": 0.8,
                "filter_documents": ["HSA_FAQ.txt"]
            }
        )
        
        # Verify response
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 1
        assert result[0]["document_name"] == "HSA_FAQ.txt"

    def test_vector_search_invalid_parameters(self, client):
        """Test vector search with invalid parameters."""
        # Test missing query
        response = client.post("/api/v1/qa/search", json={})
        assert response.status_code == 422
        
        # Test query too short
        response = client.post("/api/v1/qa/search", json={"query": "Hi"})
        assert response.status_code == 422
        
        # Test invalid k value
        response = client.post("/api/v1/qa/search", json={"query": "HSA limits", "k": 0})
        assert response.status_code == 422
        
        # Test invalid threshold value
        response = client.post("/api/v1/qa/search", json={"query": "HSA limits", "threshold": 1.5})
        assert response.status_code == 422


class TestKnowledgeBaseStatsEndpoint:
    """Test cases for /api/v1/qa/stats endpoint."""

    @patch('backend.api.v1.qa.get_rag_service')
    def test_get_knowledge_base_stats_success(self, mock_get_rag_service, client):
        """Test successful retrieval of knowledge base statistics."""
        mock_rag = AsyncMock()
        mock_stats = KnowledgeBaseStats(
            total_documents=5,
            total_chunks=50,
            total_embeddings=50,
            average_chunk_size=800.5,
            last_index_update="2024-01-01T10:00:00"
        )
        mock_rag.get_knowledge_base_stats.return_value = mock_stats
        mock_get_rag_service.return_value = mock_rag
        
        # Make request
        response = client.get("/api/v1/qa/stats")
        
        # Verify response
        assert response.status_code == 200
        result = response.json()
        
        # Verify required fields
        assert "total_documents" in result
        assert "total_chunks" in result
        assert "total_embeddings" in result
        assert "average_chunk_size" in result
        assert "last_index_update" in result
        
        # Verify values
        assert result["total_documents"] == 5
        assert result["total_chunks"] == 50
        assert result["total_embeddings"] == 50
        assert result["average_chunk_size"] == 800.5

    @patch('backend.api.v1.qa.get_rag_service')
    def test_get_knowledge_base_stats_service_error(self, mock_get_rag_service, client):
        """Test handling of service errors when getting stats."""
        mock_rag = AsyncMock()
        mock_rag.get_knowledge_base_stats.side_effect = Exception("Stats calculation failed")
        mock_get_rag_service.return_value = mock_rag
        
        # Make request
        response = client.get("/api/v1/qa/stats")
        
        # Verify error response
        assert response.status_code == 500
        assert "statistics" in response.json()["detail"].lower()


class TestRAGMetricsEndpoint:
    """Test cases for /api/v1/qa/metrics endpoint."""

    @patch('backend.api.v1.qa.get_rag_service')
    def test_get_rag_metrics_success(self, mock_get_rag_service, client):
        """Test successful retrieval of RAG system metrics."""
        mock_rag = AsyncMock()
        mock_metrics = {
            "total_queries": 150,
            "average_response_time_ms": 850.5,
            "average_confidence_score": 0.82,
            "citation_rate": 0.88,
            "knowledge_coverage": 0.65,
            "last_updated": "2024-01-01T10:00:00Z"
        }
        mock_rag.get_rag_metrics.return_value = mock_metrics
        mock_get_rag_service.return_value = mock_rag
        
        # Make request
        response = client.get("/api/v1/qa/metrics")
        
        # Verify response
        assert response.status_code == 200
        result = response.json()
        
        # Verify required fields
        assert "total_queries" in result
        assert "average_response_time_ms" in result
        assert "average_confidence_score" in result
        assert "citation_rate" in result
        assert "knowledge_coverage" in result
        assert "last_updated" in result
        
        # Verify reasonable metric values
        assert result["total_queries"] >= 0
        assert 0.0 <= result["average_confidence_score"] <= 1.0
        assert 0.0 <= result["citation_rate"] <= 1.0
        assert 0.0 <= result["knowledge_coverage"] <= 1.0


class TestKnowledgeBaseRebuild:
    """Test cases for /api/v1/qa/rebuild endpoint."""

    @patch('backend.api.v1.qa.get_rag_service')
    def test_rebuild_knowledge_base_success(self, mock_get_rag_service, client):
        """Test successful knowledge base rebuild trigger."""
        mock_rag = AsyncMock()
        mock_get_rag_service.return_value = mock_rag
        
        # Make request
        response = client.post("/api/v1/qa/rebuild")
        
        # Verify response
        assert response.status_code == 202
        result = response.json()
        assert "message" in result
        assert "rebuild started" in result["message"].lower()

    @patch('backend.api.v1.qa.get_rag_service')
    def test_rebuild_knowledge_base_error(self, mock_get_rag_service, client):
        """Test handling of rebuild scheduling errors."""
        mock_rag = AsyncMock()
        mock_get_rag_service.side_effect = Exception("Service unavailable")
        
        # Make request
        response = client.post("/api/v1/qa/rebuild")
        
        # Verify error response
        assert response.status_code == 500
        assert "rebuild" in response.json()["detail"].lower()


class TestQAHealthCheck:
    """Test cases for /api/v1/qa/health endpoint."""

    @patch('backend.api.v1.qa.get_rag_service')
    def test_qa_health_check_success(self, mock_get_rag_service, client):
        """Test successful Q&A service health check."""
        mock_rag = AsyncMock()
        mock_health = {
            "status": "healthy",
            "knowledge_base_loaded": True,
            "total_documents": 5,
            "total_chunks": 45,
            "queries_processed": 100,
            "openai_client_configured": True
        }
        mock_rag.health_check.return_value = mock_health
        mock_get_rag_service.return_value = mock_rag
        
        # Make request
        response = client.get("/api/v1/qa/health")
        
        # Verify response
        assert response.status_code == 200
        result = response.json()
        
        assert result["status"] == "healthy"
        assert result["service"] == "qa"
        assert "timestamp" in result
        assert result["knowledge_base_loaded"] is True
        assert result["total_documents"] > 0
        assert result["openai_client_configured"] is True

    @patch('backend.api.v1.qa.get_rag_service')
    def test_qa_health_check_unhealthy(self, mock_get_rag_service, client):
        """Test Q&A service health check when service is unhealthy."""
        mock_rag = AsyncMock()
        mock_rag.health_check.side_effect = Exception("Service unavailable")
        mock_get_rag_service.return_value = mock_rag
        
        # Make request
        response = client.get("/api/v1/qa/health")
        
        # Verify error response
        assert response.status_code == 503
        assert "unhealthy" in response.json()["detail"].lower()


class TestQAExampleQuestions:
    """Test cases for /api/v1/qa/examples endpoint."""

    def test_get_example_questions(self, client):
        """Test retrieval of example questions."""
        response = client.get("/api/v1/qa/examples")
        
        assert response.status_code == 200
        result = response.json()
        
        assert "example_questions" in result
        assert isinstance(result["example_questions"], list)
        assert len(result["example_questions"]) > 0
        
        # Verify questions are reasonable HSA-related examples
        questions = result["example_questions"]
        hsa_related = sum(1 for q in questions if "HSA" in q or "hsa" in q.lower())
        assert hsa_related > 0


class TestCitationValidation:
    """Test citation accuracy and completeness requirements from US-4.1."""

    @patch('backend.api.v1.qa.get_rag_service')
    def test_citations_include_required_fields(self, mock_get_rag_service, client):
        """Test that all citations include required fields."""
        mock_rag = AsyncMock()
        mock_response = QAResponse(
            answer="HSA contribution limits are defined in IRS Publication 969.",
            confidence_score=0.85,
            citations=[
                Citation(
                    document_name="HSA_FAQ.txt",
                    page_number=None,
                    excerpt="HSA contribution limits for 2024 are $4,150 for self-only coverage",
                    relevance_score=0.92
                ),
                Citation(
                    document_name="HSA_Limits.txt", 
                    page_number=1,
                    excerpt="Family coverage maximum is $8,300 per year",
                    relevance_score=0.88
                )
            ],
            source_documents=["HSA_FAQ.txt", "HSA_Limits.txt"],
            processing_time_ms=1100
        )
        mock_rag.answer_question.return_value = mock_response
        mock_get_rag_service.return_value = mock_rag
        
        # Make request
        response = client.post(
            "/api/v1/qa/ask",
            json={"question": "What are HSA contribution limits?"}
        )
        
        # Verify response
        assert response.status_code == 200
        result = response.json()
        
        # Verify citations structure
        citations = result["citations"]
        assert len(citations) == 2
        
        for citation in citations:
            # Required fields
            assert "document_name" in citation
            assert "excerpt" in citation
            assert "relevance_score" in citation
            
            # Verify data types and constraints
            assert isinstance(citation["document_name"], str)
            assert len(citation["document_name"]) > 0
            assert isinstance(citation["excerpt"], str)
            assert len(citation["excerpt"]) > 0
            assert isinstance(citation["relevance_score"], float)
            assert 0.0 <= citation["relevance_score"] <= 1.0
            
            # Optional field
            if "page_number" in citation:
                assert citation["page_number"] is None or isinstance(citation["page_number"], int)

    @patch('backend.api.v1.qa.get_rag_service')
    def test_source_documents_match_citations(self, mock_get_rag_service, client):
        """Test that source_documents list matches citation document names."""
        mock_rag = AsyncMock()
        mock_response = QAResponse(
            answer="Test answer with multiple sources",
            confidence_score=0.80,
            citations=[
                Citation(
                    document_name="HSA_FAQ.txt",
                    excerpt="Test excerpt 1",
                    relevance_score=0.90
                ),
                Citation(
                    document_name="HSA_Limits.txt",
                    excerpt="Test excerpt 2", 
                    relevance_score=0.85
                ),
                Citation(
                    document_name="HSA_FAQ.txt",  # Same document as first citation
                    excerpt="Test excerpt 3",
                    relevance_score=0.75
                )
            ],
            source_documents=["HSA_FAQ.txt", "HSA_Limits.txt"],  # Should be deduplicated
            processing_time_ms=900
        )
        mock_rag.answer_question.return_value = mock_response
        mock_get_rag_service.return_value = mock_rag
        
        # Make request
        response = client.post(
            "/api/v1/qa/ask",
            json={"question": "Test question"}
        )
        
        # Verify response
        assert response.status_code == 200
        result = response.json()
        
        # Extract unique document names from citations
        citation_documents = set(c["document_name"] for c in result["citations"])
        source_documents = set(result["source_documents"])
        
        # Verify source documents list matches unique citation documents
        assert citation_documents == source_documents

    @patch('backend.api.v1.qa.get_rag_service')
    def test_high_confidence_answers_have_citations(self, mock_get_rag_service, client):
        """Test that high-confidence answers always include citations."""
        mock_rag = AsyncMock()
        mock_response = QAResponse(
            answer="High confidence answer about HSA limits",
            confidence_score=0.95,  # High confidence
            citations=[
                Citation(
                    document_name="HSA_FAQ.txt",
                    excerpt="Detailed information about HSA limits",
                    relevance_score=0.93
                )
            ],
            source_documents=["HSA_FAQ.txt"],
            processing_time_ms=750
        )
        mock_rag.answer_question.return_value = mock_response
        mock_get_rag_service.return_value = mock_rag
        
        # Make request
        response = client.post(
            "/api/v1/qa/ask",
            json={"question": "What are HSA limits?"}
        )
        
        # Verify response
        assert response.status_code == 200
        result = response.json()
        
        # High confidence (>0.8) should have citations
        if result["confidence_score"] > 0.8:
            assert len(result["citations"]) > 0
            assert len(result["source_documents"]) > 0
        
    @patch('backend.api.v1.qa.get_rag_service')
    def test_low_confidence_answers_may_lack_citations(self, mock_get_rag_service, client):
        """Test that low-confidence answers may have no citations."""
        mock_rag = AsyncMock()
        mock_response = QAResponse(
            answer="I don't have sufficient information to answer that question accurately.",
            confidence_score=0.2,  # Low confidence
            citations=[],  # No citations for low confidence
            source_documents=[],
            processing_time_ms=400
        )
        mock_rag.answer_question.return_value = mock_response
        mock_get_rag_service.return_value = mock_rag
        
        # Make request
        response = client.post(
            "/api/v1/qa/ask",
            json={"question": "Obscure question not in knowledge base"}
        )
        
        # Verify response
        assert response.status_code == 200
        result = response.json()
        
        # Low confidence answers can have empty citations
        assert result["confidence_score"] < 0.5
        assert len(result["citations"]) == 0
        assert len(result["source_documents"]) == 0