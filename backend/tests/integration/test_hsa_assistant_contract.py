"""
Contract tests for HSA Assistant API endpoints.

This module provides comprehensive API contract validation for the HSA Assistant
service, ensuring API responses match specifications and business requirements
from user stories US-4.1 and US-4.2.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timezone

from backend.main import app
from backend.schemas.hsa_assistant import QAResponse, Citation, VectorSearchResult, KnowledgeBaseStats, RAGMetrics


@pytest.fixture
def client():
    """Test client for API endpoints."""
    return TestClient(app)


class TestHSAAssistantAPIContract:
    """API contract tests for HSA Assistant endpoints."""

    @patch('backend.api.v1.hsa_assistant.get_rag_service')
    def test_ask_endpoint_response_schema(self, mock_get_rag_service, client):
        """Test /ask endpoint returns correct response schema."""
        # Mock RAG service response
        mock_rag = AsyncMock()
        mock_response = QAResponse(
            answer="The HSA contribution limits for 2024 are $4,150 for self-only coverage and $8,300 for family coverage according to IRS Publication 969.",
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
            "/api/v1/hsa_assistant/ask",
            json={
                "question": "What are the HSA contribution limits for 2024?",
                "application_id": "test-app-123"
            }
        )
        
        # Validate contract requirements
        assert response.status_code == 200
        result = response.json()
        
        # Required fields per schema
        required_fields = ["answer", "confidence_score", "citations", "source_documents", "processing_time_ms", "created_at"]
        for field in required_fields:
            assert field in result, f"Required field '{field}' missing from response"
        
        # Data type validation
        assert isinstance(result["answer"], str)
        assert len(result["answer"]) > 0
        assert isinstance(result["confidence_score"], (int, float))
        assert 0.0 <= result["confidence_score"] <= 1.0
        assert isinstance(result["citations"], list)
        assert isinstance(result["source_documents"], list)
        assert isinstance(result["processing_time_ms"], int)
        assert result["processing_time_ms"] > 0
        
        # Citation structure validation
        for citation in result["citations"]:
            assert "document_name" in citation
            assert "excerpt" in citation
            assert "relevance_score" in citation
            assert isinstance(citation["document_name"], str)
            assert isinstance(citation["excerpt"], str)
            assert isinstance(citation["relevance_score"], (int, float))
            assert 0.0 <= citation["relevance_score"] <= 1.0

    @patch('backend.api.v1.hsa_assistant.get_rag_service')
    def test_ask_endpoint_request_validation(self, mock_get_rag_service, client):
        """Test /ask endpoint request validation."""
        mock_rag = AsyncMock()
        mock_get_rag_service.return_value = mock_rag
        
        # Test cases for request validation
        test_cases = [
            # Missing question
            ({}, 422),
            # Question too short (< 10 chars)
            ({"question": "Hi"}, 422),
            # Question too long (> 500 chars)
            ({"question": "A" * 501}, 422),
            # Context too long (> 1000 chars)
            ({"question": "Valid question", "context": "B" * 1001}, 422),
            # Valid request
            ({"question": "What are HSA contribution limits?"}, 200),
            # Valid request with context
            ({"question": "What are HSA limits?", "context": "For individual coverage"}, 200),
            # Valid request with application_id
            ({"question": "HSA eligibility rules?", "application_id": "app-123"}, 200),
        ]
        
        for request_data, expected_status in test_cases:
            if expected_status == 200:
                # Mock successful response for valid requests
                mock_response = QAResponse(
                    answer="Test answer",
                    confidence_score=0.8,
                    citations=[],
                    source_documents=[],
                    processing_time_ms=500
                )
                mock_rag.answer_question.return_value = mock_response
            
            response = client.post("/api/v1/hsa_assistant/ask", json=request_data)
            assert response.status_code == expected_status, f"Failed for request: {request_data}"

    @patch('backend.api.v1.hsa_assistant.get_rag_service')
    def test_vector_search_endpoint_contract(self, mock_get_rag_service, client):
        """Test /search endpoint API contract."""
        mock_rag = AsyncMock()
        mock_results = [
            VectorSearchResult(
                chunk_id="chunk_1",
                document_name="HSA_FAQ.txt",
                text="HSA contribution limits for 2024 are $4,150 for self-only coverage",
                similarity_score=0.95,
                metadata={"chunk_index": 0}
            )
        ]
        mock_rag.vector_search.return_value = mock_results
        mock_get_rag_service.return_value = mock_rag
        
        # Make valid request
        response = client.post(
            "/api/v1/hsa_assistant/search",
            json={
                "query": "HSA contribution limits",
                "k": 5,
                "threshold": 0.7
            }
        )
        
        # Validate contract
        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)
        
        # Validate result structure
        for item in result:
            required_fields = ["chunk_id", "document_name", "text", "similarity_score", "metadata"]
            for field in required_fields:
                assert field in item
            
            assert isinstance(item["chunk_id"], str)
            assert isinstance(item["document_name"], str)
            assert isinstance(item["text"], str)
            assert isinstance(item["similarity_score"], (int, float))
            assert 0.0 <= item["similarity_score"] <= 1.0
            assert isinstance(item["metadata"], dict)

    def test_vector_search_request_validation(self, client):
        """Test /search endpoint request validation."""
        test_cases = [
            # Missing query
            ({}, 422),
            # Query too short (< 3 chars)
            ({"query": "Hi"}, 422),
            # Query too long (> 500 chars)
            ({"query": "A" * 501}, 422),
            # Invalid k value (< 1)
            ({"query": "HSA limits", "k": 0}, 422),
            # Invalid k value (> 20)
            ({"query": "HSA limits", "k": 25}, 422),
            # Invalid threshold (< 0.0)
            ({"query": "HSA limits", "threshold": -0.1}, 422),
            # Invalid threshold (> 1.0)
            ({"query": "HSA limits", "threshold": 1.5}, 422),
        ]
        
        for request_data, expected_status in test_cases:
            response = client.post("/api/v1/hsa_assistant/search", json=request_data)
            assert response.status_code == expected_status

    @patch('backend.api.v1.hsa_assistant.get_rag_service')
    def test_stats_endpoint_contract(self, mock_get_rag_service, client):
        """Test /stats endpoint API contract."""
        mock_rag = AsyncMock()
        mock_stats = KnowledgeBaseStats(
            total_documents=5,
            total_chunks=50,
            total_embeddings=50,
            average_chunk_size=800.5,
            last_index_update=datetime.now(timezone.utc)
        )
        mock_rag.get_knowledge_base_stats.return_value = mock_stats
        mock_get_rag_service.return_value = mock_rag
        
        response = client.get("/api/v1/hsa_assistant/stats")
        
        assert response.status_code == 200
        result = response.json()
        
        # Validate required fields
        required_fields = ["total_documents", "total_chunks", "total_embeddings", "average_chunk_size", "last_index_update"]
        for field in required_fields:
            assert field in result
        
        # Validate data types and constraints
        assert isinstance(result["total_documents"], int)
        assert result["total_documents"] >= 0
        assert isinstance(result["total_chunks"], int)
        assert result["total_chunks"] >= 0
        assert isinstance(result["total_embeddings"], int)
        assert result["total_embeddings"] >= 0
        assert isinstance(result["average_chunk_size"], (int, float))
        assert result["average_chunk_size"] >= 0.0

    @patch('backend.api.v1.hsa_assistant.get_rag_service')
    def test_metrics_endpoint_contract(self, mock_get_rag_service, client):
        """Test /metrics endpoint API contract."""
        mock_rag = AsyncMock()
        mock_metrics = RAGMetrics(
            total_queries=150,
            average_response_time_ms=850.5,
            average_confidence_score=0.82,
            citation_rate=0.88,
            knowledge_coverage=0.65,
            last_updated=datetime.now(timezone.utc)
        )
        mock_rag.get_rag_metrics.return_value = mock_metrics
        mock_get_rag_service.return_value = mock_rag
        
        response = client.get("/api/v1/hsa_assistant/metrics")
        
        assert response.status_code == 200
        result = response.json()
        
        # Validate required fields
        required_fields = ["total_queries", "average_response_time_ms", "average_confidence_score", "citation_rate", "knowledge_coverage", "last_updated"]
        for field in required_fields:
            assert field in result
        
        # Validate data types and constraints
        assert isinstance(result["total_queries"], int)
        assert result["total_queries"] >= 0
        assert isinstance(result["average_response_time_ms"], (int, float))
        assert result["average_response_time_ms"] >= 0.0
        assert isinstance(result["average_confidence_score"], (int, float))
        assert 0.0 <= result["average_confidence_score"] <= 1.0
        assert isinstance(result["citation_rate"], (int, float))
        assert 0.0 <= result["citation_rate"] <= 1.0
        assert isinstance(result["knowledge_coverage"], (int, float))
        assert 0.0 <= result["knowledge_coverage"] <= 1.0

    def test_history_endpoint_contract(self, client):
        """Test /history/{application_id} endpoint API contract."""
        response = client.get("/api/v1/hsa_assistant/history/test-app-123")
        
        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)
        
        # If history items exist, validate structure
        for item in result:
            required_fields = ["id", "question", "answer", "confidence_score", "citations_count", "created_at"]
            for field in required_fields:
                assert field in item
            
            assert isinstance(item["id"], str)
            assert isinstance(item["question"], str)
            assert isinstance(item["answer"], str)
            assert isinstance(item["confidence_score"], (int, float))
            assert 0.0 <= item["confidence_score"] <= 1.0
            assert isinstance(item["citations_count"], int)
            assert item["citations_count"] >= 0

    def test_history_endpoint_pagination(self, client):
        """Test /history endpoint pagination parameters."""
        # Test with pagination parameters
        response = client.get("/api/v1/hsa_assistant/history/test-app-123?limit=10&offset=5")
        assert response.status_code == 200
        
        # Test with invalid pagination
        response = client.get("/api/v1/hsa_assistant/history/test-app-123?limit=-1")
        # Should handle gracefully (either 200 with empty results or 422)
        assert response.status_code in [200, 422]

    def test_rebuild_endpoint_contract(self, client):
        """Test /rebuild endpoint API contract."""
        with patch('backend.api.v1.hsa_assistant.get_rag_service') as mock_get_rag_service:
            mock_rag = AsyncMock()
            mock_get_rag_service.return_value = mock_rag
            
            response = client.post("/api/v1/hsa_assistant/rebuild")
            
            assert response.status_code == 202
            result = response.json()
            assert "message" in result
            assert isinstance(result["message"], str)

    @patch('backend.api.v1.hsa_assistant.get_rag_service')
    def test_health_endpoint_contract(self, mock_get_rag_service, client):
        """Test /health endpoint API contract."""
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
        
        response = client.get("/api/v1/hsa_assistant/health")
        
        assert response.status_code == 200
        result = response.json()
        
        # Validate required fields
        required_fields = ["status", "service", "timestamp"]
        for field in required_fields:
            assert field in result
        
        assert result["service"] == "hsa_assistant"
        assert isinstance(result["status"], str)
        assert isinstance(result["timestamp"], str)

    def test_examples_endpoint_contract(self, client):
        """Test /examples endpoint API contract."""
        response = client.get("/api/v1/hsa_assistant/examples")
        
        assert response.status_code == 200
        result = response.json()
        
        assert "example_questions" in result
        assert isinstance(result["example_questions"], list)
        assert len(result["example_questions"]) > 0
        
        # Validate example questions are strings
        for question in result["example_questions"]:
            assert isinstance(question, str)
            assert len(question) > 0


class TestHSAAssistantBusinessRules:
    """Tests for HSA Assistant business rules from user stories."""

    @patch('backend.api.v1.hsa_assistant.get_rag_service')
    def test_hsa_contribution_limit_question_accuracy(self, mock_get_rag_service, client):
        """Test accuracy of HSA contribution limit responses per US-4.1."""
        mock_rag = AsyncMock()
        mock_response = QAResponse(
            answer="For 2024, HSA contribution limits are $4,150 for self-only coverage and $8,300 for family coverage, as specified in IRS Publication 969.",
            confidence_score=0.95,
            citations=[
                Citation(
                    document_name="HSA_FAQ.txt",
                    excerpt="HSA contribution limits for 2024 are $4,150 for self-only coverage and $8,300 for family coverage",
                    relevance_score=0.96
                )
            ],
            source_documents=["HSA_FAQ.txt"],
            processing_time_ms=1200
        )
        mock_rag.answer_question.return_value = mock_response
        mock_get_rag_service.return_value = mock_rag
        
        # Test contribution limit questions
        contribution_questions = [
            "What are the HSA contribution limits for 2024?",
            "How much can I contribute to my HSA?",
            "What is the maximum HSA contribution limit?",
        ]
        
        for question in contribution_questions:
            response = client.post(
                "/api/v1/hsa_assistant/ask",
                json={"question": question}
            )
            
            assert response.status_code == 200
            result = response.json()
            
            # Should have high confidence for contribution limit questions
            assert result["confidence_score"] > 0.8
            # Answer should contain specific amounts
            assert any(amount in result["answer"] for amount in ["4,150", "4150", "8,300", "8300"])
            # Should have citations
            assert len(result["citations"]) > 0

    @patch('backend.api.v1.hsa_assistant.get_rag_service')
    def test_hsa_eligibility_question_accuracy(self, mock_get_rag_service, client):
        """Test accuracy of HSA eligibility responses per US-4.1."""
        mock_rag = AsyncMock()
        mock_response = QAResponse(
            answer="To be eligible for an HSA, you must be covered under a qualified high-deductible health plan (HDHP), have no other health coverage except permitted coverage, not be enrolled in Medicare, and not be claimed as a dependent on another person's tax return.",
            confidence_score=0.90,
            citations=[
                Citation(
                    document_name="HSA_Eligibility.txt",
                    excerpt="HSA eligibility requires HDHP coverage and no other health coverage",
                    relevance_score=0.92
                )
            ],
            source_documents=["HSA_Eligibility.txt"],
            processing_time_ms=950
        )
        mock_rag.answer_question.return_value = mock_response
        mock_get_rag_service.return_value = mock_rag
        
        # Test eligibility questions
        eligibility_questions = [
            "Am I eligible for an HSA?",
            "What are the HSA eligibility requirements?",
            "Can I open an HSA with my current health plan?",
        ]
        
        for question in eligibility_questions:
            response = client.post(
                "/api/v1/hsa_assistant/ask",
                json={"question": question}
            )
            
            assert response.status_code == 200
            result = response.json()
            
            # Should have reasonable confidence for eligibility questions
            assert result["confidence_score"] > 0.7
            # Answer should contain eligibility criteria
            eligibility_terms = ["HDHP", "high-deductible", "health plan", "coverage", "eligible"]
            assert any(term.lower() in result["answer"].lower() for term in eligibility_terms)
            # Should have citations
            assert len(result["citations"]) > 0

    @patch('backend.api.v1.hsa_assistant.get_rag_service')
    def test_fallback_handling_for_unknown_questions(self, mock_get_rag_service, client):
        """Test fallback handling for questions without answers per US-4.1."""
        mock_rag = AsyncMock()
        mock_response = QAResponse(
            answer="I don't have information about that in my HSA knowledge base. Please rephrase your question or ask about HSA eligibility, contribution limits, qualified expenses, or account management.",
            confidence_score=0.0,
            citations=[],
            source_documents=[],
            processing_time_ms=300
        )
        mock_rag.answer_question.return_value = mock_response
        mock_get_rag_service.return_value = mock_rag
        
        # Test non-HSA questions
        non_hsa_questions = [
            "What is the capital of France?",
            "How do I cook pasta?",
            "What's the weather today?",
            "Tell me a joke",
        ]
        
        for question in non_hsa_questions:
            response = client.post(
                "/api/v1/hsa_assistant/ask",
                json={"question": question}
            )
            
            assert response.status_code == 200
            result = response.json()
            
            # Should have low/zero confidence
            assert result["confidence_score"] <= 0.2
            # Should indicate lack of information
            assert "don't have information" in result["answer"].lower() or "don't know" in result["answer"].lower()
            # Should have no citations for unknown topics
            assert len(result["citations"]) == 0
            assert len(result["source_documents"]) == 0

    @patch('backend.api.v1.hsa_assistant.get_rag_service')
    def test_response_includes_proper_citations(self, mock_get_rag_service, client):
        """Test that responses include proper citations per US-4.1."""
        mock_rag = AsyncMock()
        mock_response = QAResponse(
            answer="According to HSA_FAQ.txt, the HSA contribution limits for 2024 are specified in IRS guidelines.",
            confidence_score=0.88,
            citations=[
                Citation(
                    document_name="HSA_FAQ.txt",
                    excerpt="HSA contribution limits for 2024 are $4,150 for self-only coverage",
                    relevance_score=0.94
                ),
                Citation(
                    document_name="IRS_Guidelines.txt", 
                    excerpt="IRS sets annual HSA contribution limits",
                    relevance_score=0.89
                )
            ],
            source_documents=["HSA_FAQ.txt", "IRS_Guidelines.txt"],
            processing_time_ms=1100
        )
        mock_rag.answer_question.return_value = mock_response
        mock_get_rag_service.return_value = mock_rag
        
        response = client.post(
            "/api/v1/hsa_assistant/ask",
            json={"question": "What are HSA contribution limits?"}
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # High confidence answers should have citations
        if result["confidence_score"] > 0.7:
            assert len(result["citations"]) > 0
            assert len(result["source_documents"]) > 0
            
            # Citations should be relevant (high relevance scores)
            for citation in result["citations"]:
                assert citation["relevance_score"] > 0.7
                assert len(citation["excerpt"]) > 0
                assert len(citation["document_name"]) > 0

    @patch('backend.api.v1.hsa_assistant.get_rag_service')
    def test_processing_time_tracking(self, mock_get_rag_service, client):
        """Test that processing times are tracked for performance monitoring."""
        mock_rag = AsyncMock()
        mock_response = QAResponse(
            answer="Test answer",
            confidence_score=0.85,
            citations=[],
            source_documents=[],
            processing_time_ms=750  # Specific processing time
        )
        mock_rag.answer_question.return_value = mock_response
        mock_get_rag_service.return_value = mock_rag
        
        response = client.post(
            "/api/v1/hsa_assistant/ask",
            json={"question": "Test question"}
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Processing time should be tracked
        assert "processing_time_ms" in result
        assert isinstance(result["processing_time_ms"], int)
        assert result["processing_time_ms"] > 0
        # Should be reasonable (not too slow)
        assert result["processing_time_ms"] < 30000  # Less than 30 seconds


class TestHSAAssistantErrorHandling:
    """Tests for error handling scenarios."""

    @patch('backend.api.v1.hsa_assistant.get_rag_service')
    def test_rag_service_unavailable(self, mock_get_rag_service, client):
        """Test handling when RAG service is unavailable."""
        mock_get_rag_service.side_effect = Exception("RAG service unavailable")
        
        response = client.post(
            "/api/v1/hsa_assistant/ask",
            json={"question": "What are HSA limits?"}
        )
        
        assert response.status_code == 500
        result = response.json()
        assert "detail" in result

    @patch('backend.api.v1.hsa_assistant.get_rag_service')
    def test_openai_api_error_handling(self, mock_get_rag_service, client):
        """Test handling of OpenAI API errors."""
        mock_rag = AsyncMock()
        mock_rag.answer_question.side_effect = Exception("OpenAI API error")
        mock_get_rag_service.return_value = mock_rag
        
        response = client.post(
            "/api/v1/hsa_assistant/ask",
            json={"question": "What are HSA limits?"}
        )
        
        assert response.status_code == 500
        result = response.json()
        assert "error occurred" in result["detail"].lower()

    def test_malformed_json_request(self, client):
        """Test handling of malformed JSON requests."""
        response = client.post(
            "/api/v1/hsa_assistant/ask",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422

    def test_missing_content_type(self, client):
        """Test handling of requests without content type."""
        response = client.post(
            "/api/v1/hsa_assistant/ask",
            data='{"question": "test"}'
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 422, 415]


class TestHSAAssistantPerformance:
    """Performance-related tests."""

    @patch('backend.api.v1.hsa_assistant.get_rag_service')
    def test_response_time_reasonable(self, mock_get_rag_service, client):
        """Test that API response times are reasonable."""
        import time
        
        mock_rag = AsyncMock()
        mock_response = QAResponse(
            answer="Test answer",
            confidence_score=0.8,
            citations=[],
            source_documents=[],
            processing_time_ms=500
        )
        mock_rag.answer_question.return_value = mock_response
        mock_get_rag_service.return_value = mock_rag
        
        start_time = time.time()
        response = client.post(
            "/api/v1/hsa_assistant/ask",
            json={"question": "What are HSA limits?"}
        )
        end_time = time.time()
        
        assert response.status_code == 200
        # API should respond within 10 seconds (including mocking overhead)
        assert (end_time - start_time) < 10.0

    @patch('backend.api.v1.hsa_assistant.get_rag_service')
    def test_concurrent_requests_handling(self, mock_get_rag_service, client):
        """Test handling of concurrent requests."""
        import concurrent.futures
        import threading
        
        mock_rag = AsyncMock()
        mock_response = QAResponse(
            answer="Test answer",
            confidence_score=0.8,
            citations=[],
            source_documents=[],
            processing_time_ms=100
        )
        mock_rag.answer_question.return_value = mock_response
        mock_get_rag_service.return_value = mock_rag
        
        def make_request():
            return client.post(
                "/api/v1/hsa_assistant/ask",
                json={"question": "What are HSA limits?"}
            )
        
        # Make 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            responses = [future.result() for future in futures]
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200