"""
End-to-end tests for OpenAI Vector Stores RAG workflow.

Tests the complete workflow from vector store creation through file upload 
to query processing, validating the OpenAI Vector Stores API integration
as specified in user stories US-4.1 and US-4.2.

These tests simulate real workflow patterns but use mocked OpenAI API calls
to ensure reliable, deterministic testing.
"""

import pytest
import os
import tempfile
import shutil
import asyncio
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime

from backend.services.openai_vector_store_service import (
    OpenAIVectorStoreService, OpenAIVectorStoreError
)
from backend.schemas.hsa_assistant import (
    QARequest, QAResponse, Citation, VectorSearchRequest, 
    KnowledgeBaseStats, RAGMetrics
)


class TestOpenAIE2EWorkflow:
    """End-to-end workflow tests for OpenAI Vector Stores integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.knowledge_base_path = Path(self.temp_dir) / "knowledge_base" / "hsa"
        self.knowledge_base_path.mkdir(parents=True)
        
        # Create realistic IRS PDF content
        self.irs_pdf_path = self.knowledge_base_path / "irs.pdf"
        self.irs_pdf_path.write_bytes(
            b"Mock IRS Publication 969 - Health Savings Accounts and Other Tax-Favored Health Plans\n"
            b"This document contains comprehensive information about HSA contribution limits,\n"
            b"eligibility requirements, qualified expenses, and account management rules."
        )

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'})
    @patch('backend.services.openai_vector_store_service.OpenAI')
    @pytest.mark.asyncio
    async def test_complete_workflow_from_scratch(self, mock_openai_class):
        """Test complete workflow: create vector store -> upload PDF -> query -> get stats."""
        # Set up comprehensive OpenAI API mocks
        mock_client = self._setup_comprehensive_openai_mock(mock_openai_class)
        
        # Initialize service without pre-existing vector store
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        service.vector_store_id = None  # Start fresh
        
        # Step 1: Create vector store
        vector_store_id = await service.create_vector_store("hsa_knowledge_base_e2e")
        assert vector_store_id == "vs_e2e_123"
        assert service.vector_store_id == "vs_e2e_123"
        
        # Step 2: Upload knowledge base (IRS PDF)
        await service.upload_knowledge_base()
        
        # Step 3: Answer multiple questions to test various scenarios
        questions_and_expected = [
            ("What are the HSA contribution limits for 2024?", "4,150", "8,300"),
            ("Am I eligible for an HSA?", "high-deductible", "eligible"),
            ("Can I use HSA for dental expenses?", "qualified", "dental"),
        ]
        
        responses = []
        for question, *expected_terms in questions_and_expected:
            request = QARequest(question=question, application_id=f"e2e-test-{len(responses)}")
            response = await service.answer_question(request)
            responses.append(response)
            
            # Verify response quality
            assert isinstance(response, QAResponse)
            assert response.confidence_score > 0.0
            assert len(response.citations) > 0
            assert "irs.pdf" in response.source_documents
            assert response.processing_time_ms > 0
            
            # Verify answer contains expected terms
            answer_lower = response.answer.lower()
            for term in expected_terms:
                assert term.lower() in answer_lower or term.replace(",", "") in answer_lower
        
        # Step 4: Perform vector search
        search_request = VectorSearchRequest(query="HSA contribution limits", k=3, threshold=0.7)
        search_results = await service.vector_search(search_request)
        
        assert len(search_results) > 0
        assert all(result.document_name == "irs.pdf" for result in search_results)
        assert all(result.similarity_score >= 0.5 for result in search_results)
        
        # Step 5: Get knowledge base statistics
        stats = await service.get_knowledge_base_stats()
        assert isinstance(stats, KnowledgeBaseStats)
        assert stats.total_documents == 1  # IRS PDF
        assert stats.total_chunks > 0
        assert stats.total_embeddings > 0
        
        # Step 6: Get RAG metrics
        metrics = await service.get_rag_metrics()
        assert isinstance(metrics, RAGMetrics)
        assert metrics.total_queries == 3  # Three questions asked
        assert metrics.average_response_time_ms > 0
        assert 0.0 <= metrics.average_confidence_score <= 1.0
        assert metrics.knowledge_coverage == 1.0  # Full coverage with IRS PDF
        
        # Step 7: Test rebuild workflow
        await service.rebuild_knowledge_base()
        
        # Verify all OpenAI API interactions occurred
        self._verify_openai_api_calls(mock_client, expected_questions=3)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key', 'OPENAI_VECTOR_STORE_ID': 'vs_existing_456'})
    @patch('backend.services.openai_vector_store_service.OpenAI')
    @pytest.mark.asyncio
    async def test_workflow_with_existing_vector_store(self, mock_openai_class):
        """Test workflow when vector store already exists."""
        # Set up OpenAI API mocks
        mock_client = self._setup_comprehensive_openai_mock(mock_openai_class)
        
        # Initialize service with existing vector store ID
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        assert service.vector_store_id == "vs_existing_456"
        
        # Should be able to directly upload without creating new vector store
        await service.upload_knowledge_base()
        
        # Should be able to answer questions immediately
        request = QARequest(question="What are HSA eligibility requirements?")
        response = await service.answer_question(request)
        
        assert isinstance(response, QAResponse)
        assert response.confidence_score > 0.0
        assert len(response.citations) > 0
        
        # Verify vector store creation was NOT called (using existing)
        mock_client.beta.vector_stores.create.assert_not_called()

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'})
    @patch('backend.services.openai_vector_store_service.OpenAI')
    @pytest.mark.asyncio
    async def test_workflow_error_recovery(self, mock_openai_class):
        """Test error handling and recovery in complete workflow."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        
        # Test 1: Vector store creation failure
        mock_client.beta.vector_stores.create.side_effect = Exception("API Error")
        
        with pytest.raises(OpenAIVectorStoreError, match="Vector store creation failed"):
            await service.create_vector_store("test_store")
        
        # Test 2: File upload failure
        mock_client.beta.vector_stores.create.side_effect = None
        mock_client.beta.vector_stores.create.return_value.id = "vs_test_789"
        mock_client.files.create.side_effect = Exception("Upload failed")
        
        with pytest.raises(OpenAIVectorStoreError, match="Knowledge base upload failed"):
            await service.upload_knowledge_base()
        
        # Test 3: Query failure after successful setup
        mock_client.files.create.side_effect = None
        mock_client.files.create.return_value.id = "file_test_789"
        mock_client.beta.vector_stores.files.create.return_value.id = "vf_test_789"
        
        # Mock successful file processing
        mock_file_status = MagicMock()
        mock_file_status.status = "completed"
        mock_client.beta.vector_stores.files.retrieve.return_value = mock_file_status
        
        # Setup should succeed now
        await service.upload_knowledge_base()
        
        # But query should fail
        mock_client.beta.chat.completions.create.side_effect = Exception("Query failed")
        
        request = QARequest(question="Test question")
        with pytest.raises(OpenAIVectorStoreError, match="Question answering failed"):
            await service.answer_question(request)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'})
    @patch('backend.services.openai_vector_store_service.OpenAI')
    @pytest.mark.asyncio
    async def test_concurrent_queries_workflow(self, mock_openai_class):
        """Test handling of concurrent queries in workflow."""
        # Set up OpenAI API mocks
        mock_client = self._setup_comprehensive_openai_mock(mock_openai_class)
        
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        service.vector_store_id = "vs_concurrent_test"
        
        # Create multiple concurrent query tasks
        questions = [
            "What are HSA contribution limits?",
            "Who is eligible for an HSA?",
            "What are qualified HSA expenses?",
            "Can I roll over HSA funds?",
            "How do I open an HSA account?"
        ]
        
        # Execute queries concurrently
        tasks = []
        for i, question in enumerate(questions):
            request = QARequest(question=question, application_id=f"concurrent-{i}")
            task = asyncio.create_task(service.answer_question(request))
            tasks.append(task)
        
        # Wait for all queries to complete
        responses = await asyncio.gather(*tasks)
        
        # Verify all responses are valid
        assert len(responses) == 5
        for i, response in enumerate(responses):
            assert isinstance(response, QAResponse)
            assert response.confidence_score > 0.0
            assert len(response.citations) > 0
            assert response.processing_time_ms > 0
        
        # Verify metrics reflect all queries
        metrics = await service.get_rag_metrics()
        assert metrics.total_queries == 5

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'})
    @patch('backend.services.openai_vector_store_service.OpenAI')
    @pytest.mark.asyncio
    async def test_health_check_throughout_workflow(self, mock_openai_class):
        """Test health check status at different workflow stages."""
        mock_client = self._setup_comprehensive_openai_mock(mock_openai_class)
        
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        
        # Health check before any setup
        health = await service.health_check()
        assert health["status"] in ["degraded", "unhealthy"]  # No vector store yet
        assert health["vector_store_initialized"] is False
        
        # Create vector store
        await service.create_vector_store("health_test_store")
        
        # Health check after vector store creation
        health = await service.health_check()
        assert health["vector_store_initialized"] is True
        # May still be degraded until files are uploaded
        
        # Upload knowledge base
        await service.upload_knowledge_base()
        
        # Health check after full setup
        health = await service.health_check()
        assert health["status"] == "healthy"
        assert health["vector_store_initialized"] is True
        assert health["vector_store_healthy"] is True
        assert health["openai_client_configured"] is True
        assert health["knowledge_base_path_exists"] is True

    def _setup_comprehensive_openai_mock(self, mock_openai_class):
        """Set up comprehensive OpenAI API mocks for workflow testing."""
        mock_client = MagicMock()
        
        # Mock vector store creation
        mock_vector_store = MagicMock()
        mock_vector_store.id = "vs_e2e_123"
        mock_vector_store.status = "completed"
        mock_client.beta.vector_stores.create.return_value = mock_vector_store
        mock_client.beta.vector_stores.retrieve.return_value = mock_vector_store
        
        # Mock file upload
        mock_uploaded_file = MagicMock()
        mock_uploaded_file.id = "file_e2e_123"
        mock_client.files.create.return_value = mock_uploaded_file
        
        # Mock file attachment to vector store
        mock_vector_store_file = MagicMock()
        mock_vector_store_file.id = "vf_e2e_123"
        mock_client.beta.vector_stores.files.create.return_value = mock_vector_store_file
        
        # Mock file processing completion
        mock_file_status = MagicMock()
        mock_file_status.status = "completed"
        mock_client.beta.vector_stores.files.retrieve.return_value = mock_file_status
        
        # Mock chat completions for different questions
        def create_mock_response(question):
            if "contribution limits" in question.lower():
                content = "For 2024, HSA contribution limits are $4,150 for self-only coverage and $8,300 for family coverage, as specified in IRS Publication 969."
            elif "eligible" in question.lower():
                content = "To be eligible for an HSA, you must be covered under a qualified high-deductible health plan and meet other IRS requirements."
            elif "dental" in question.lower():
                content = "Yes, dental expenses are qualified HSA expenses when they are primarily for medical care."
            else:
                content = f"Information about your question is available in IRS Publication 969."
            
            mock_message = MagicMock()
            mock_message.content = content
            mock_message.annotations = []
            
            mock_choice = MagicMock()
            mock_choice.message = mock_message
            
            mock_response = MagicMock()
            mock_response.choices = [mock_choice]
            return mock_response
        
        mock_client.beta.chat.completions.create.side_effect = lambda **kwargs: create_mock_response(
            kwargs.get('messages', [{}])[-1].get('content', '')
        )
        
        # Mock vector search
        mock_tool_call = MagicMock()
        mock_tool_call.type = "file_search"
        mock_tool_call.id = "call_search_123"
        mock_tool_call.function.arguments = "HSA contribution limits information"
        
        mock_search_message = MagicMock()
        mock_search_message.tool_calls = [mock_tool_call]
        mock_search_response = MagicMock()
        mock_search_response.choices = [MagicMock(message=mock_search_message)]
        
        # Override chat completions for search queries
        original_create = mock_client.beta.chat.completions.create.side_effect
        def create_with_search_handling(**kwargs):
            if kwargs.get('tool_choice') == 'required':
                return mock_search_response
            return original_create(**kwargs)
        
        mock_client.beta.chat.completions.create.side_effect = create_with_search_handling
        
        # Mock vector store stats
        mock_file_counts = MagicMock()
        mock_file_counts.completed = 25
        mock_vector_store.file_counts = mock_file_counts
        
        mock_files_response = MagicMock()
        mock_files_response.data = [MagicMock()]  # One file (IRS PDF)
        mock_client.beta.vector_stores.files.list.return_value = mock_files_response
        
        mock_openai_class.return_value = mock_client
        return mock_client

    def _verify_openai_api_calls(self, mock_client, expected_questions=1):
        """Verify expected OpenAI API calls were made."""
        # Verify vector store creation
        mock_client.beta.vector_stores.create.assert_called()
        
        # Verify file upload
        mock_client.files.create.assert_called()
        
        # Verify file attachment
        mock_client.beta.vector_stores.files.create.assert_called()
        
        # Verify file processing status check
        mock_client.beta.vector_stores.files.retrieve.assert_called()
        
        # Verify chat completions for questions
        assert mock_client.beta.chat.completions.create.call_count >= expected_questions
        
        # Verify vector store retrieval for stats
        mock_client.beta.vector_stores.retrieve.assert_called()
        
        # Verify files listing for stats
        mock_client.beta.vector_stores.files.list.assert_called()


class TestOpenAIE2EPerformance:
    """Performance and scaling tests for OpenAI Vector Stores workflow."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.knowledge_base_path = Path(self.temp_dir) / "knowledge_base" / "hsa"
        self.knowledge_base_path.mkdir(parents=True)
        
        # Create IRS PDF
        self.irs_pdf_path = self.knowledge_base_path / "irs.pdf"
        self.irs_pdf_path.write_bytes(b"Mock IRS Publication 969 content")

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key', 'OPENAI_VECTOR_STORE_ID': 'vs_perf_test'})
    @patch('backend.services.openai_vector_store_service.OpenAI')
    @pytest.mark.asyncio
    async def test_high_volume_query_performance(self, mock_openai_class):
        """Test performance with high volume of queries."""
        # Set up fast-responding mock
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Fast response about HSA"
        mock_message.annotations = []
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=mock_message)]
        mock_client.beta.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        
        # Execute many queries quickly
        num_queries = 50
        start_time = datetime.utcnow()
        
        tasks = []
        for i in range(num_queries):
            request = QARequest(question=f"HSA question {i}", application_id=f"perf-test-{i}")
            task = asyncio.create_task(service.answer_question(request))
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        end_time = datetime.utcnow()
        
        # Verify all responses
        assert len(responses) == num_queries
        for response in responses:
            assert isinstance(response, QAResponse)
            assert response.processing_time_ms > 0
        
        # Check performance metrics
        metrics = await service.get_rag_metrics()
        assert metrics.total_queries == num_queries
        
        # Total time should be reasonable (allowing for async execution)
        total_time_ms = (end_time - start_time).total_seconds() * 1000
        avg_time_per_query = total_time_ms / num_queries
        
        # With proper async execution, average should be much less than sequential
        assert avg_time_per_query < 1000  # Less than 1 second average

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key', 'OPENAI_VECTOR_STORE_ID': 'vs_mem_test'})
    @patch('backend.services.openai_vector_store_service.OpenAI')
    @pytest.mark.asyncio
    async def test_memory_usage_with_many_queries(self, mock_openai_class):
        """Test memory usage doesn't grow unbounded with many queries."""
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "HSA response"
        mock_message.annotations = []
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=mock_message)]
        mock_client.beta.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        
        # Execute queries and check metrics tracking
        for i in range(100):
            request = QARequest(question=f"HSA question {i}")
            await service.answer_question(request)
            
            # Check that confidence scores list doesn't grow unbounded
            # (in production, you might want to limit history)
            if i > 50:
                # Confidence scores should be tracking recent queries
                assert len(service.confidence_scores) <= 100  # Some reasonable limit
        
        # Verify metrics are properly calculated
        metrics = await service.get_rag_metrics()
        assert metrics.total_queries == 100
        assert 0.0 <= metrics.average_confidence_score <= 1.0


class TestOpenAIE2EDataFlow:
    """Test data flow and transformation through complete OpenAI workflow."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.knowledge_base_path = Path(self.temp_dir) / "knowledge_base" / "hsa"
        self.knowledge_base_path.mkdir(parents=True)
        
        # Create IRS PDF with specific content to trace
        self.irs_pdf_path = self.knowledge_base_path / "irs.pdf"
        self.test_content = (
            b"IRS Publication 969 - Health Savings Accounts\n"
            b"2024 HSA Contribution Limits:\n"
            b"- Self-only coverage: $4,150\n"
            b"- Family coverage: $8,300\n"
            b"- Additional catch-up contribution (age 55+): $1,000\n"
            b"\nHSA Eligibility Requirements:\n"
            b"- Must be covered under qualified HDHP\n"
            b"- No other health coverage\n"
            b"- Not enrolled in Medicare\n"
        )
        self.irs_pdf_path.write_bytes(self.test_content)

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'})
    @patch('backend.services.openai_vector_store_service.OpenAI')
    @pytest.mark.asyncio
    async def test_data_flow_from_pdf_to_response(self, mock_openai_class):
        """Test that data flows correctly from PDF through OpenAI to final response."""
        # Set up mock to simulate realistic data flow
        mock_client = MagicMock()
        
        # Mock vector store creation
        mock_vector_store = MagicMock()
        mock_vector_store.id = "vs_dataflow_123"
        mock_client.beta.vector_stores.create.return_value = mock_vector_store
        
        # Mock file upload - verify PDF content is read
        mock_uploaded_file = MagicMock()
        mock_uploaded_file.id = "file_dataflow_123"
        
        def capture_file_upload(*args, **kwargs):
            # Verify the file being uploaded contains our test content
            file_obj = kwargs.get('file')
            if file_obj:
                content = file_obj.read()
                assert b"2024 HSA Contribution Limits" in content
                assert b"$4,150" in content
                assert b"$8,300" in content
                file_obj.seek(0)  # Reset file pointer
            return mock_uploaded_file
        
        mock_client.files.create.side_effect = capture_file_upload
        
        # Mock file attachment and processing
        mock_vector_store_file = MagicMock()
        mock_vector_store_file.id = "vf_dataflow_123"
        mock_client.beta.vector_stores.files.create.return_value = mock_vector_store_file
        
        mock_file_status = MagicMock()
        mock_file_status.status = "completed"
        mock_client.beta.vector_stores.files.retrieve.return_value = mock_file_status
        
        # Mock chat completion with realistic response based on our test content
        def create_contextual_response(**kwargs):
            messages = kwargs.get('messages', [])
            user_message = messages[-1].get('content', '') if messages else ''
            
            # Generate response that reflects the test PDF content
            if "contribution limits" in user_message.lower():
                content = "Based on IRS Publication 969, the 2024 HSA contribution limits are $4,150 for self-only coverage and $8,300 for family coverage. An additional catch-up contribution of $1,000 is allowed for individuals age 55 and older."
            elif "eligibility" in user_message.lower():
                content = "According to IRS Publication 969, HSA eligibility requires being covered under a qualified high-deductible health plan (HDHP), having no other health coverage, and not being enrolled in Medicare."
            else:
                content = "Information is available in IRS Publication 969 regarding HSA rules and regulations."
            
            mock_message = MagicMock()
            mock_message.content = content
            # Mock annotations that would come from file_search tool
            mock_annotation = MagicMock()
            mock_annotation.file_citation = MagicMock()
            mock_annotation.text = "HSA contribution limits are $4,150 for self-only coverage"
            mock_message.annotations = [mock_annotation]
            
            mock_choice = MagicMock()
            mock_choice.message = mock_message
            
            mock_response = MagicMock()
            mock_response.choices = [mock_choice]
            return mock_response
        
        mock_client.beta.chat.completions.create.side_effect = create_contextual_response
        mock_openai_class.return_value = mock_client
        
        # Execute workflow
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        
        # Create and upload
        await service.create_vector_store("dataflow_test")
        await service.upload_knowledge_base()
        
        # Test contribution limits query
        request = QARequest(question="What are the HSA contribution limits for 2024?")
        response = await service.answer_question(request)
        
        # Verify response reflects our test PDF content
        assert "4,150" in response.answer or "4150" in response.answer
        assert "8,300" in response.answer or "8300" in response.answer
        assert "1,000" in response.answer or "1000" in response.answer
        assert len(response.citations) > 0
        assert response.citations[0].document_name == "irs.pdf"
        assert "irs.pdf" in response.source_documents
        
        # Test eligibility query
        request = QARequest(question="What are HSA eligibility requirements?")
        response = await service.answer_question(request)
        
        # Verify response reflects eligibility content
        assert "high-deductible health plan" in response.answer.lower() or "hdhp" in response.answer.lower()
        assert "medicare" in response.answer.lower()
        assert len(response.citations) > 0

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'})
    @patch('backend.services.openai_vector_store_service.OpenAI')
    @pytest.mark.asyncio
    async def test_citation_accuracy_with_real_content(self, mock_openai_class):
        """Test that citations accurately reflect the source content."""
        mock_client = MagicMock()
        
        # Set up mocks for upload workflow
        mock_vector_store = MagicMock()
        mock_vector_store.id = "vs_citation_test"
        mock_client.beta.vector_stores.create.return_value = mock_vector_store
        mock_client.files.create.return_value.id = "file_citation_test"
        mock_client.beta.vector_stores.files.create.return_value.id = "vf_citation_test"
        
        mock_file_status = MagicMock()
        mock_file_status.status = "completed"
        mock_client.beta.vector_stores.files.retrieve.return_value = mock_file_status
        
        # Mock response with detailed annotations
        mock_message = MagicMock()
        mock_message.content = "HSA contribution limits for 2024 are detailed in the IRS guidelines."
        
        # Create realistic annotations that would come from our PDF content
        mock_annotation1 = MagicMock()
        mock_annotation1.file_citation = MagicMock()
        mock_annotation1.text = "Self-only coverage: $4,150 maximum annual contribution"
        
        mock_annotation2 = MagicMock()
        mock_annotation2.file_citation = MagicMock()
        mock_annotation2.text = "Family coverage: $8,300 maximum annual contribution"
        
        mock_message.annotations = [mock_annotation1, mock_annotation2]
        mock_client.beta.chat.completions.create.return_value.choices = [MagicMock(message=mock_message)]
        
        mock_openai_class.return_value = mock_client
        
        # Execute workflow
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        await service.create_vector_store("citation_test")
        await service.upload_knowledge_base()
        
        # Ask question and verify citations
        request = QARequest(question="What are the HSA contribution limits?")
        response = await service.answer_question(request)
        
        # Verify citations match the annotation content
        assert len(response.citations) == 2
        
        citation_texts = [c.excerpt for c in response.citations]
        assert any("4,150" in text or "4150" in text for text in citation_texts)
        assert any("8,300" in text or "8300" in text for text in citation_texts)
        
        # All citations should reference IRS PDF
        assert all(c.document_name == "irs.pdf" for c in response.citations)
        assert all(c.relevance_score > 0.8 for c in response.citations)  # High relevance from annotations

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'})
    @patch('backend.services.openai_vector_store_service.OpenAI')
    @pytest.mark.asyncio
    async def test_workflow_state_consistency(self, mock_openai_class):
        """Test that service state remains consistent throughout workflow."""
        mock_client = self._setup_basic_openai_mock(mock_openai_class)
        
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        
        # Track initial state
        initial_query_count = service.query_count
        initial_total_time = service.total_response_time
        initial_confidence_scores = len(service.confidence_scores)
        
        # Execute workflow steps
        await service.create_vector_store("state_test")
        assert service.vector_store_id == "vs_state_test"
        
        await service.upload_knowledge_base()
        
        # State should be preserved
        assert service.query_count == initial_query_count
        assert service.total_response_time == initial_total_time
        assert len(service.confidence_scores) == initial_confidence_scores
        
        # Execute queries
        for i in range(3):
            request = QARequest(question=f"HSA question {i}")
            response = await service.answer_question(request)
            
            # Verify state updates correctly
            assert service.query_count == initial_query_count + i + 1
            assert service.total_response_time > initial_total_time
            assert len(service.confidence_scores) == initial_confidence_scores + i + 1
            
            # Verify response processing time is tracked
            assert response.processing_time_ms > 0
        
        # Verify final metrics consistency
        metrics = await service.get_rag_metrics()
        assert metrics.total_queries == service.query_count
        assert metrics.average_response_time_ms == service.total_response_time / service.query_count
        assert metrics.average_confidence_score == sum(service.confidence_scores) / len(service.confidence_scores)

    def _setup_basic_openai_mock(self, mock_openai_class):
        """Set up basic OpenAI mock for workflow testing."""
        mock_client = MagicMock()
        
        # Mock vector store operations
        mock_vector_store = MagicMock()
        mock_vector_store.id = "vs_state_test"
        mock_client.beta.vector_stores.create.return_value = mock_vector_store
        
        # Mock file operations
        mock_client.files.create.return_value.id = "file_state_test"
        mock_client.beta.vector_stores.files.create.return_value.id = "vf_state_test"
        
        mock_file_status = MagicMock()
        mock_file_status.status = "completed"
        mock_client.beta.vector_stores.files.retrieve.return_value = mock_file_status
        
        # Mock chat completions
        mock_message = MagicMock()
        mock_message.content = "HSA information from IRS Publication 969"
        mock_message.annotations = []
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=mock_message)]
        mock_client.beta.chat.completions.create.return_value = mock_response
        
        mock_openai_class.return_value = mock_client
        return mock_client