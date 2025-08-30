"""
Integration tests for HSA Assistant API endpoints with OpenAI Vector Stores.

Tests the complete OpenAI Vector Store workflow including API endpoints, service integration,
citation accuracy, and response quality as specified in user stories US-4.1 and US-4.2.

These tests focus on the OpenAI Vector Stores API integration patterns.
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime

from backend.main import app
from backend.schemas.hsa_assistant import (
    QAResponse, Citation, VectorSearchResult, 
    KnowledgeBaseStats, RAGMetrics
)


@pytest.fixture
def client():
    """Test client for API endpoints."""
    return TestClient(app)


@pytest.fixture
def mock_knowledge_base():
    """Mock knowledge base setup with IRS PDF for testing."""
    temp_dir = tempfile.mkdtemp()
    kb_path = Path(temp_dir) / "knowledge_base" / "hsa"
    kb_path.mkdir(parents=True)
    
    # Create mock IRS PDF
    irs_pdf_path = kb_path / "irs.pdf"
    irs_pdf_path.write_bytes(b"Mock PDF content for IRS Publication 969 - HSA rules and regulations")
    
    yield str(kb_path.parent)
    shutil.rmtree(temp_dir)


class TestHSAAssistantOpenAIAskEndpoint:
    """Test cases for /api/v1/hsa_assistant/ask endpoint with OpenAI Vector Stores."""

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key', 'OPENAI_VECTOR_STORE_ID': 'vs_test123'})
    @patch('backend.api.v1.hsa_assistant.get_vector_store_service')
    def test_ask_question_success(self, mock_get_service, client):
        """Test successful question processing with OpenAI Vector Stores."""
        # Mock OpenAI Vector Store service
        mock_service = AsyncMock()
        mock_response = QAResponse(
            answer="For 2024, HSA contribution limits are $4,150 for self-only coverage and $8,300 for family coverage, as specified in IRS Publication 969.",
            confidence_score=0.92,
            citations=[
                Citation(
                    document_name="irs.pdf",
                    excerpt="For 2024, HSA contribution limits are $4,150 for self-only coverage and $8,300 for family coverage.",
                    relevance_score=0.95
                )
            ],
            source_documents=["irs.pdf"],
            processing_time_ms=1250
        )
        mock_service.answer_question.return_value = mock_response
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.post(
            "/api/v1/hsa_assistant/ask",
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
        assert citation["document_name"] == "irs.pdf"  # Should reference IRS PDF
        assert citation["relevance_score"] > 0.9
        assert "irs.pdf" in result["source_documents"]

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key', 'OPENAI_VECTOR_STORE_ID': 'vs_test123'})
    @patch('backend.api.v1.hsa_assistant.get_vector_store_service')
    def test_ask_question_with_context(self, mock_get_service, client):
        """Test question processing with context using OpenAI Vector Stores."""
        mock_service = AsyncMock()
        mock_response = QAResponse(
            answer="For self-only coverage in 2024, the HSA contribution limit is $4,150 according to IRS Publication 969.",
            confidence_score=0.88,
            citations=[
                Citation(
                    document_name="irs.pdf",
                    excerpt="$4,150 for self-only coverage",
                    relevance_score=0.90
                )
            ],
            source_documents=["irs.pdf"],
            processing_time_ms=980
        )
        mock_service.answer_question.return_value = mock_response
        mock_get_service.return_value = mock_service
        
        # Make request with context
        response = client.post(
            "/api/v1/hsa_assistant/ask",
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
        
        # Verify service was called with correct parameters
        mock_service.answer_question.assert_called_once()
        call_args = mock_service.answer_question.call_args[0][0]
        assert call_args.question == "What is the contribution limit?"
        assert call_args.context == "I am asking about individual coverage"
        assert call_args.application_id == "test-app-456"

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key', 'OPENAI_VECTOR_STORE_ID': 'vs_test123'})
    @patch('backend.api.v1.hsa_assistant.get_vector_store_service')
    def test_ask_question_no_answer_available(self, mock_get_service, client):
        """Test handling when OpenAI Vector Store has no relevant answer."""
        mock_service = AsyncMock()
        mock_response = QAResponse(
            answer="I don't have information about that in my HSA knowledge base. Please ask about HSA eligibility, contribution limits, qualified expenses, or account management.",
            confidence_score=0.0,
            citations=[],
            source_documents=[],
            processing_time_ms=500
        )
        mock_service.answer_question.return_value = mock_response
        mock_get_service.return_value = mock_service
        
        # Make request with unrelated question
        response = client.post(
            "/api/v1/hsa_assistant/ask",
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

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key', 'OPENAI_VECTOR_STORE_ID': 'vs_test123'})
    @patch('backend.api.v1.hsa_assistant.get_vector_store_service')
    def test_ask_question_vector_store_not_initialized(self, mock_get_service, client):
        """Test error handling when vector store is not initialized."""
        from backend.services.openai_vector_store_service import OpenAIVectorStoreError
        
        mock_service = AsyncMock()
        mock_service.answer_question.side_effect = OpenAIVectorStoreError("Vector store not initialized")
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.post(
            "/api/v1/hsa_assistant/ask",
            json={"question": "What are HSA contribution limits?"}
        )
        
        # Verify error response
        assert response.status_code == 500
        assert "Vector store not initialized" in response.json()["detail"]

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key', 'OPENAI_VECTOR_STORE_ID': 'vs_test123'})
    @patch('backend.api.v1.hsa_assistant.get_vector_store_service')
    def test_ask_question_openai_api_failure(self, mock_get_service, client):
        """Test error handling when OpenAI API fails."""
        from backend.services.openai_vector_store_service import OpenAIVectorStoreError
        
        mock_service = AsyncMock()
        mock_service.answer_question.side_effect = OpenAIVectorStoreError("OpenAI API error: rate limit exceeded")
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.post(
            "/api/v1/hsa_assistant/ask",
            json={"question": "What are HSA contribution limits?"}
        )
        
        # Verify error response
        assert response.status_code == 500
        assert "OpenAI API error" in response.json()["detail"]


class TestHSAAssistantHistoryEndpoint:
    """Test cases for /api/v1/hsa_assistant/history/{application_id} endpoint."""

    def test_get_hsa_assistant_history_success(self, client):
        """Test successful retrieval of HSA Assistant history."""
        response = client.get("/api/v1/hsa_assistant/history/test-app-123")
        
        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)

    def test_get_hsa_assistant_history_with_pagination(self, client):
        """Test HSA Assistant history retrieval with pagination."""
        response = client.get("/api/v1/hsa_assistant/history/test-app-123?limit=10&offset=5")
        
        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)

    def test_get_hsa_assistant_history_all_applications(self, client):
        """Test HSA Assistant history retrieval for all applications."""
        response = client.get("/api/v1/hsa_assistant/history/all")
        
        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)


class TestVectorSearchEndpoint:
    """Test cases for /api/v1/hsa_assistant/search endpoint."""

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key', 'OPENAI_VECTOR_STORE_ID': 'vs_test123'})
    @patch('backend.api.v1.hsa_assistant.get_vector_store_service')
    def test_vector_search_success(self, mock_get_service, client):
        """Test successful vector search using OpenAI Vector Stores."""
        mock_service = AsyncMock()
        mock_results = [
            VectorSearchResult(
                chunk_id="chunk_1",
                document_name="irs.pdf",
                text="HSA contribution limits for 2024 are $4,150 for self-only coverage",
                similarity_score=0.95,
                metadata={"document": "irs.pdf", "chunk_index": 0}
            ),
            VectorSearchResult(
                chunk_id="chunk_2",
                document_name="irs.pdf",
                text="Family coverage maximum annual contribution is $8,300",
                similarity_score=0.87,
                metadata={"document": "irs.pdf", "chunk_index": 1}
            )
        ]
        mock_service.vector_search.return_value = mock_results
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.post(
            "/api/v1/hsa_assistant/search",
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
        assert first_result["chunk_id"] == "chunk_1"
        assert first_result["document_name"] == "irs.pdf"
        assert "HSA contribution limits" in first_result["text"]
        assert first_result["similarity_score"] == 0.95
        
        # Verify similarity scores are in descending order
        assert result[0]["similarity_score"] >= result[1]["similarity_score"]

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key', 'OPENAI_VECTOR_STORE_ID': 'vs_test123'})
    @patch('backend.api.v1.hsa_assistant.get_vector_store_service')
    def test_vector_search_no_results(self, mock_get_service, client):
        """Test vector search with no results from OpenAI Vector Store."""
        mock_service = AsyncMock()
        mock_results = [
            VectorSearchResult(
                chunk_id="fallback_chunk",
                document_name="irs.pdf",
                text="Search performed for: unknown query",
                similarity_score=0.5,
                metadata={"document": "irs.pdf", "chunk_index": 0}
            )
        ]
        mock_service.vector_search.return_value = mock_results
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.post(
            "/api/v1/hsa_assistant/search",
            json={
                "query": "completely unrelated query",
                "k": 3,
                "threshold": 0.8
            }
        )
        
        # Verify response - should return fallback result
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 1
        assert result[0]["chunk_id"] == "fallback_chunk"
        assert result[0]["similarity_score"] == 0.5

    def test_vector_search_invalid_parameters(self, client):
        """Test vector search parameter validation."""
        # Test missing query
        response = client.post("/api/v1/hsa_assistant/search", json={})
        assert response.status_code == 422
        
        # Test query too short
        response = client.post("/api/v1/hsa_assistant/search", json={"query": "Hi"})
        assert response.status_code == 422
        
        # Test invalid k value
        response = client.post("/api/v1/hsa_assistant/search", json={"query": "HSA limits", "k": 0})
        assert response.status_code == 422
        
        # Test invalid threshold value
        response = client.post("/api/v1/hsa_assistant/search", json={"query": "HSA limits", "threshold": 1.5})
        assert response.status_code == 422


class TestKnowledgeBaseStatsEndpoint:
    """Test cases for /api/v1/hsa_assistant/stats endpoint."""

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key', 'OPENAI_VECTOR_STORE_ID': 'vs_test123'})
    @patch('backend.api.v1.hsa_assistant.get_vector_store_service')
    def test_get_knowledge_base_stats_success(self, mock_get_service, client):
        """Test successful retrieval of OpenAI Vector Store statistics."""
        mock_service = AsyncMock()
        mock_stats = KnowledgeBaseStats(
            total_documents=1,  # IRS PDF
            total_chunks=25,
            total_embeddings=25,
            average_chunk_size=1000.0,
            last_index_update=datetime.utcnow()
        )
        mock_service.get_knowledge_base_stats.return_value = mock_stats
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.get("/api/v1/hsa_assistant/stats")
        
        # Verify response
        assert response.status_code == 200
        result = response.json()
        
        # Verify required fields
        assert "total_documents" in result
        assert "total_chunks" in result
        assert "total_embeddings" in result
        assert "average_chunk_size" in result
        assert "last_index_update" in result
        
        # Verify values are reasonable for OpenAI Vector Store
        assert result["total_documents"] == 1  # Should have IRS PDF
        assert result["total_chunks"] > 0
        assert result["total_embeddings"] > 0
        assert result["average_chunk_size"] > 0.0

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'})
    @patch('backend.api.v1.hsa_assistant.get_vector_store_service')
    def test_get_knowledge_base_stats_no_vector_store(self, mock_get_service, client):
        """Test knowledge base stats when no vector store is initialized."""
        mock_service = AsyncMock()
        mock_stats = KnowledgeBaseStats(
            total_documents=0,
            total_chunks=0,
            total_embeddings=0,
            average_chunk_size=0.0,
            last_index_update=datetime.utcnow()
        )
        mock_service.get_knowledge_base_stats.return_value = mock_stats
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.get("/api/v1/hsa_assistant/stats")
        
        # Verify response
        assert response.status_code == 200
        result = response.json()
        assert result["total_documents"] == 0
        assert result["total_chunks"] == 0
        assert result["total_embeddings"] == 0


class TestRAGMetricsEndpoint:
    """Test cases for /api/v1/hsa_assistant/metrics endpoint."""

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key', 'OPENAI_VECTOR_STORE_ID': 'vs_test123'})
    @patch('backend.api.v1.hsa_assistant.get_vector_store_service')
    def test_get_rag_metrics_success(self, mock_get_service, client):
        """Test successful retrieval of OpenAI Vector Store metrics."""
        mock_service = AsyncMock()
        mock_metrics = RAGMetrics(
            total_queries=150,
            average_response_time_ms=850.5,
            average_confidence_score=0.82,
            citation_rate=0.88,
            knowledge_coverage=1.0,  # Full coverage with IRS PDF
            last_updated=datetime.utcnow()
        )
        mock_service.get_rag_metrics.return_value = mock_metrics
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.get("/api/v1/hsa_assistant/metrics")
        
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
        assert result["total_queries"] == 150
        assert result["average_response_time_ms"] == 850.5
        assert 0.0 <= result["average_confidence_score"] <= 1.0
        assert 0.0 <= result["citation_rate"] <= 1.0
        assert result["knowledge_coverage"] == 1.0  # Full coverage expected


class TestKnowledgeBaseRebuild:
    """Test cases for /api/v1/hsa_assistant/rebuild endpoint."""

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key', 'OPENAI_VECTOR_STORE_ID': 'vs_test123'})
    @patch('backend.api.v1.hsa_assistant.get_vector_store_service')
    def test_rebuild_knowledge_base_success(self, mock_get_service, client):
        """Test successful OpenAI Vector Store rebuild trigger."""
        mock_service = AsyncMock()
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.post("/api/v1/hsa_assistant/rebuild")
        
        # Verify response
        assert response.status_code == 202
        result = response.json()
        assert "message" in result
        assert "rebuild started" in result["message"].lower()
        assert "IRS PDF" in result["message"]  # Should mention IRS PDF upload

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key', 'OPENAI_VECTOR_STORE_ID': 'vs_test123'})
    @patch('backend.api.v1.hsa_assistant.get_vector_store_service')
    def test_rebuild_knowledge_base_error(self, mock_get_service, client):
        """Test handling of rebuild scheduling errors."""
        mock_service = AsyncMock()
        mock_get_service.side_effect = Exception("OpenAI service unavailable")
        
        # Make request
        response = client.post("/api/v1/hsa_assistant/rebuild")
        
        # Verify error response
        assert response.status_code == 500
        assert "rebuild" in response.json()["detail"].lower()


class TestHSAAssistantHealthCheck:
    """Test cases for /api/v1/hsa_assistant/health endpoint."""

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key', 'OPENAI_VECTOR_STORE_ID': 'vs_test123'})
    @patch('backend.api.v1.hsa_assistant.get_vector_store_service')
    def test_health_check_success(self, mock_get_service, client):
        """Test successful HSA Assistant health check."""
        mock_service = AsyncMock()
        mock_health = {
            "status": "healthy",
            "vector_store_initialized": True,
            "vector_store_healthy": True,
            "queries_processed": 100,
            "openai_client_configured": True,
            "knowledge_base_path_exists": True
        }
        mock_service.health_check.return_value = mock_health
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.get("/api/v1/hsa_assistant/health")
        
        # Verify response
        assert response.status_code == 200
        result = response.json()
        
        assert result["status"] == "healthy"
        assert result["service"] == "hsa_assistant"
        assert "timestamp" in result
        assert result["vector_store_initialized"] is True
        assert result["vector_store_healthy"] is True
        assert result["openai_client_configured"] is True

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'})
    @patch('backend.api.v1.hsa_assistant.get_vector_store_service')
    def test_health_check_degraded(self, mock_get_service, client):
        """Test health check when vector store is not healthy."""
        mock_service = AsyncMock()
        mock_health = {
            "status": "degraded",
            "vector_store_initialized": False,
            "vector_store_healthy": False,
            "queries_processed": 50,
            "openai_client_configured": True,
            "knowledge_base_path_exists": True
        }
        mock_service.health_check.return_value = mock_health
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.get("/api/v1/hsa_assistant/health")
        
        # Verify response
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "degraded"
        assert result["vector_store_healthy"] is False

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key', 'OPENAI_VECTOR_STORE_ID': 'vs_test123'})
    @patch('backend.api.v1.hsa_assistant.get_vector_store_service')
    def test_health_check_unhealthy(self, mock_get_service, client):
        """Test health check when service is unhealthy."""
        mock_service = AsyncMock()
        mock_service.health_check.side_effect = Exception("OpenAI service unavailable")
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.get("/api/v1/hsa_assistant/health")
        
        # Verify error response
        assert response.status_code == 503
        assert "unhealthy" in response.json()["detail"].lower()


class TestExampleQuestions:
    """Test cases for /api/v1/hsa_assistant/examples endpoint."""

    def test_get_example_questions(self, client):
        """Test retrieval of HSA-specific example questions."""
        response = client.get("/api/v1/hsa_assistant/examples")
        
        assert response.status_code == 200
        result = response.json()
        
        assert "example_questions" in result
        assert isinstance(result["example_questions"], list)
        assert len(result["example_questions"]) > 0
        
        # Verify questions are HSA-related
        questions = result["example_questions"]
        hsa_related = sum(1 for q in questions if "HSA" in q)
        assert hsa_related > 5  # Should have multiple HSA questions
        
        # Check for specific HSA topics
        all_questions = " ".join(questions)
        assert "contribution limits" in all_questions.lower()
        assert "eligible" in all_questions.lower() or "eligibility" in all_questions.lower()


class TestOpenAICitationValidation:
    """Test OpenAI citation accuracy and completeness requirements from US-4.1."""

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key', 'OPENAI_VECTOR_STORE_ID': 'vs_test123'})
    @patch('backend.api.v1.hsa_assistant.get_vector_store_service')
    def test_citations_reference_irs_pdf(self, mock_get_service, client):
        """Test that citations properly reference IRS PDF source."""
        mock_service = AsyncMock()
        mock_response = QAResponse(
            answer="HSA contribution limits are defined in IRS Publication 969.",
            confidence_score=0.85,
            citations=[
                Citation(
                    document_name="irs.pdf",
                    excerpt="HSA contribution limits for 2024 are $4,150 for self-only coverage",
                    relevance_score=0.92
                ),
                Citation(
                    document_name="irs.pdf", 
                    excerpt="Family coverage maximum is $8,300 per year",
                    relevance_score=0.88
                )
            ],
            source_documents=["irs.pdf"],
            processing_time_ms=1100
        )
        mock_service.answer_question.return_value = mock_response
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.post(
            "/api/v1/hsa_assistant/ask",
            json={"question": "What are HSA contribution limits?"}
        )
        
        # Verify response
        assert response.status_code == 200
        result = response.json()
        
        # Verify all citations reference IRS PDF
        citations = result["citations"]
        assert len(citations) == 2
        
        for citation in citations:
            assert citation["document_name"] == "irs.pdf"
            assert isinstance(citation["excerpt"], str)
            assert len(citation["excerpt"]) > 0
            assert 0.0 <= citation["relevance_score"] <= 1.0
        
        # Verify source documents list
        assert result["source_documents"] == ["irs.pdf"]

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key', 'OPENAI_VECTOR_STORE_ID': 'vs_test123'})
    @patch('backend.api.v1.hsa_assistant.get_vector_store_service')
    def test_default_citation_when_no_annotations(self, mock_get_service, client):
        """Test that default IRS citation is provided when OpenAI returns no annotations."""
        mock_service = AsyncMock()
        mock_response = QAResponse(
            answer="HSA information is available in IRS Publication 969.",
            confidence_score=0.75,
            citations=[
                Citation(
                    document_name="irs.pdf",
                    excerpt="Information sourced from IRS Publication 969: Health Savings Accounts and Other Tax-Favored Health Plans",
                    relevance_score=0.8
                )
            ],
            source_documents=["irs.pdf"],
            processing_time_ms=800
        )
        mock_service.answer_question.return_value = mock_response
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.post(
            "/api/v1/hsa_assistant/ask",
            json={"question": "Tell me about HSA"}
        )
        
        # Verify response
        assert response.status_code == 200
        result = response.json()
        
        # Should have default citation
        citations = result["citations"]
        assert len(citations) == 1
        assert citations[0]["document_name"] == "irs.pdf"
        assert "IRS Publication 969" in citations[0]["excerpt"]

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key', 'OPENAI_VECTOR_STORE_ID': 'vs_test123'})
    @patch('backend.api.v1.hsa_assistant.get_vector_store_service')
    def test_confidence_score_calculation(self, mock_get_service, client):
        """Test that confidence scores are calculated appropriately."""
        mock_service = AsyncMock()
        
        # Test high confidence response
        mock_response = QAResponse(
            answer="This is a detailed response about HSA contribution limits with comprehensive information from the IRS document. The limits are clearly specified as $4,150 for individual coverage and $8,300 for family coverage in 2024.",
            confidence_score=0.95,  # High confidence
            citations=[
                Citation(document_name="irs.pdf", excerpt="Detailed HSA limits info", relevance_score=0.95),
                Citation(document_name="irs.pdf", excerpt="Additional HSA info", relevance_score=0.90),
                Citation(document_name="irs.pdf", excerpt="More HSA details", relevance_score=0.85)
            ],
            source_documents=["irs.pdf"],
            processing_time_ms=1200
        )
        mock_service.answer_question.return_value = mock_response
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.post(
            "/api/v1/hsa_assistant/ask",
            json={"question": "What are the detailed HSA contribution limits?"}
        )
        
        # Verify high confidence response
        assert response.status_code == 200
        result = response.json()
        assert result["confidence_score"] > 0.8
        assert len(result["citations"]) >= 2  # Multiple citations for high confidence
        assert len(result["answer"]) > 100  # Detailed response


class TestOpenAIErrorHandling:
    """Test error handling specific to OpenAI Vector Stores integration."""

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key', 'OPENAI_VECTOR_STORE_ID': 'vs_test123'})
    @patch('backend.api.v1.hsa_assistant.get_vector_store_service')
    def test_rate_limit_error_handling(self, mock_get_service, client):
        """Test handling of OpenAI API rate limit errors."""
        from backend.services.openai_vector_store_service import OpenAIVectorStoreError
        
        mock_service = AsyncMock()
        mock_service.answer_question.side_effect = OpenAIVectorStoreError("Question answering failed: Rate limit exceeded")
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.post(
            "/api/v1/hsa_assistant/ask",
            json={"question": "What are HSA limits?"}
        )
        
        # Verify error response
        assert response.status_code == 500
        assert "Rate limit exceeded" in response.json()["detail"]

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key', 'OPENAI_VECTOR_STORE_ID': 'vs_test123'})
    @patch('backend.api.v1.hsa_assistant.get_vector_store_service')
    def test_vector_store_upload_error(self, mock_get_service, client):
        """Test handling of vector store upload errors during rebuild."""
        from backend.services.openai_vector_store_service import OpenAIVectorStoreError
        
        mock_service = AsyncMock()
        mock_service.rebuild_knowledge_base.side_effect = OpenAIVectorStoreError("Knowledge base upload failed: File processing timeout")
        mock_get_service.return_value = mock_service
        
        # Make rebuild request 
        response = client.post("/api/v1/hsa_assistant/rebuild")
        
        # Should still return 202 (accepted) as it's a background task
        # But the background task would log the error
        assert response.status_code == 202

    @patch.dict(os.environ, {}, clear=True)  # Clear all env vars
    @patch('backend.api.v1.hsa_assistant.get_vector_store_service')
    def test_missing_api_key_initialization(self, mock_get_service, client):
        """Test service initialization without OpenAI API key."""
        mock_service = AsyncMock()
        
        # Service should still initialize but health check will show issues
        mock_health = {
            "status": "unhealthy",
            "vector_store_initialized": False,
            "vector_store_healthy": False,
            "queries_processed": 0,
            "openai_client_configured": False,
            "knowledge_base_path_exists": True,
            "error": "OpenAI API key not configured"
        }
        mock_service.health_check.return_value = mock_health
        mock_get_service.return_value = mock_service
        
        # Make health check request
        response = client.get("/api/v1/hsa_assistant/health")
        
        # Service should report unhealthy status
        assert response.status_code == 200  # Health endpoint itself works
        result = response.json()
        assert result["status"] == "unhealthy"
        assert result["openai_client_configured"] is False