"""
Unit tests for OpenAI Vector Store Service.

Tests the OpenAI Vector Stores API integration for the HSA Q&A system,
including vector store creation, file upload, query processing, and citation handling
as specified in user stories US-4.1 and US-4.2.

OpenAI Vector Store Requirements Tested:
- Vector store creation and management
- File upload (two-step process) with IRS PDF
- Assistant creation and configuration
- Query processing with file_search tool
- Citation extraction from OpenAI responses
- Error handling for OpenAI API failures
- Performance metrics collection
"""

import pytest
import asyncio
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from datetime import datetime

from backend.services.openai_vector_store_service import (
    OpenAIVectorStoreService, OpenAIVectorStoreError
)
from backend.schemas.hsa_assistant import (
    QARequest, QAResponse, Citation, VectorSearchRequest, VectorSearchResult,
    KnowledgeBaseStats, RAGMetrics
)


class TestOpenAIVectorStoreService:
    """Test cases for OpenAI Vector Store Service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.knowledge_base_path = Path(self.temp_dir) / "knowledge_base" / "hsa"
        self.knowledge_base_path.mkdir(parents=True)
        
        # Create mock IRS PDF
        self.irs_pdf_path = self.knowledge_base_path / "irs.pdf"
        self.irs_pdf_path.write_bytes(b"Mock PDF content for IRS Publication 969")
        
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-api-key',
            'OPENAI_VECTOR_STORE_ID': 'vs_test123'
        })
        self.env_patcher.start()

    def teardown_method(self):
        """Clean up test fixtures."""
        self.env_patcher.stop()
        shutil.rmtree(self.temp_dir)

    @patch('backend.services.openai_vector_store_service.OpenAI')
    def test_service_initialization(self, mock_openai_class):
        """Test OpenAI Vector Store service initialization."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        
        assert service.knowledge_base_path == self.knowledge_base_path
        assert service.vector_store_id == 'vs_test123'
        assert service.response_model == "gpt-4o-mini"
        assert service.query_count == 0
        assert service.total_response_time == 0.0
        assert service.confidence_scores == []
        
        # Verify OpenAI client was initialized with API key
        mock_openai_class.assert_called_once_with(api_key='test-api-key')

    @patch('backend.services.openai_vector_store_service.OpenAI')
    @pytest.mark.asyncio
    async def test_create_vector_store_success(self, mock_openai_class):
        """Test successful vector store creation."""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_vector_stores = MagicMock()
        mock_vector_store = MagicMock()
        mock_vector_store.id = "vs_new123"
        
        mock_vector_stores.create.return_value = mock_vector_store
        mock_client.beta.vector_stores = mock_vector_stores
        mock_openai_class.return_value = mock_client
        
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        vector_store_id = await service.create_vector_store("test_store")
        
        assert vector_store_id == "vs_new123"
        assert service.vector_store_id == "vs_new123"
        
        # Verify OpenAI API was called correctly
        mock_vector_stores.create.assert_called_once_with(name="test_store")

    @patch('backend.services.openai_vector_store_service.OpenAI')
    @pytest.mark.asyncio
    async def test_create_vector_store_failure(self, mock_openai_class):
        """Test vector store creation failure."""
        # Mock OpenAI client to raise exception
        mock_client = MagicMock()
        mock_vector_stores = MagicMock()
        mock_vector_stores.create.side_effect = Exception("API Error")
        mock_client.beta.vector_stores = mock_vector_stores
        mock_openai_class.return_value = mock_client
        
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        
        with pytest.raises(OpenAIVectorStoreError, match="Vector store creation failed"):
            await service.create_vector_store("test_store")

    @patch('backend.services.openai_vector_store_service.OpenAI')
    @pytest.mark.asyncio
    async def test_upload_knowledge_base_success(self, mock_openai_class):
        """Test successful knowledge base upload."""
        # Mock OpenAI client
        mock_client = MagicMock()
        
        # Mock file upload
        mock_files = MagicMock()
        mock_uploaded_file = MagicMock()
        mock_uploaded_file.id = "file_123"
        mock_files.create.return_value = mock_uploaded_file
        mock_client.files = mock_files
        
        # Mock vector store file attachment
        mock_vector_store_files = MagicMock()
        mock_vector_store_file = MagicMock()
        mock_vector_store_file.id = "vf_123"
        mock_vector_store_files.create.return_value = mock_vector_store_file
        mock_client.beta.vector_stores.files = mock_vector_store_files
        
        mock_openai_class.return_value = mock_client
        
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        service.vector_store_id = "vs_existing123"
        
        # Mock the wait for file processing method
        with patch.object(service, '_wait_for_file_processing') as mock_wait:
            mock_wait.return_value = None
            
            await service.upload_knowledge_base()
            
            # Verify file was uploaded
            mock_files.create.assert_called_once()
            upload_call = mock_files.create.call_args
            assert upload_call[1]['purpose'] == 'assistants'
            
            # Verify file was attached to vector store
            mock_vector_store_files.create.assert_called_once_with(
                vector_store_id="vs_existing123",
                file_id="file_123"
            )
            
            # Verify wait for processing was called
            mock_wait.assert_called_once_with("vf_123")

    @patch('backend.services.openai_vector_store_service.OpenAI')
    @pytest.mark.asyncio
    async def test_upload_knowledge_base_missing_pdf(self, mock_openai_class):
        """Test knowledge base upload with missing IRS PDF."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Remove the IRS PDF
        self.irs_pdf_path.unlink()
        
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        
        with pytest.raises(OpenAIVectorStoreError, match="IRS PDF not found"):
            await service.upload_knowledge_base()

    @patch('backend.services.openai_vector_store_service.OpenAI')
    @pytest.mark.asyncio
    async def test_upload_knowledge_base_recreate(self, mock_openai_class):
        """Test knowledge base upload with recreation."""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        service.vector_store_id = "vs_existing123"
        
        # Mock create_vector_store and upload methods
        with patch.object(service, 'create_vector_store') as mock_create:
            mock_create.return_value = "vs_new123"
            
            with patch.object(service, '_wait_for_file_processing') as mock_wait:
                mock_wait.return_value = None
                
                # Mock file operations
                mock_client.files.create.return_value.id = "file_123"
                mock_client.beta.vector_stores.files.create.return_value.id = "vf_123"
                
                await service.upload_knowledge_base(recreate=True)
                
                # Verify vector store was recreated
                mock_create.assert_called_once()
                assert service.vector_store_id == "vs_new123"

    @patch('backend.services.openai_vector_store_service.OpenAI')
    @pytest.mark.asyncio
    async def test_wait_for_file_processing_success(self, mock_openai_class):
        """Test successful file processing wait."""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_vector_store_files = MagicMock()
        
        # Mock file status progression: in_progress -> completed
        mock_file_status = MagicMock()
        mock_file_status.status = "completed"
        mock_vector_store_files.retrieve.return_value = mock_file_status
        
        mock_client.beta.vector_stores.files = mock_vector_store_files
        mock_openai_class.return_value = mock_client
        
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        service.vector_store_id = "vs_test123"
        
        # Should complete without raising exception
        await service._wait_for_file_processing("vf_123")
        
        # Verify status was checked
        mock_vector_store_files.retrieve.assert_called_with(
            vector_store_id="vs_test123",
            file_id="vf_123"
        )

    @patch('backend.services.openai_vector_store_service.OpenAI')
    @pytest.mark.asyncio
    async def test_wait_for_file_processing_failure(self, mock_openai_class):
        """Test file processing failure."""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_vector_store_files = MagicMock()
        
        # Mock file status as failed
        mock_file_status = MagicMock()
        mock_file_status.status = "failed"
        mock_vector_store_files.retrieve.return_value = mock_file_status
        
        mock_client.beta.vector_stores.files = mock_vector_store_files
        mock_openai_class.return_value = mock_client
        
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        service.vector_store_id = "vs_test123"
        
        with pytest.raises(OpenAIVectorStoreError, match="File processing failed"):
            await service._wait_for_file_processing("vf_123")

    @patch('backend.services.openai_vector_store_service.OpenAI')
    @pytest.mark.asyncio
    async def test_wait_for_file_processing_timeout(self, mock_openai_class):
        """Test file processing timeout."""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_vector_store_files = MagicMock()
        
        # Mock file status as always in_progress
        mock_file_status = MagicMock()
        mock_file_status.status = "in_progress"
        mock_vector_store_files.retrieve.return_value = mock_file_status
        
        mock_client.beta.vector_stores.files = mock_vector_store_files
        mock_openai_class.return_value = mock_client
        
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        service.vector_store_id = "vs_test123"
        
        # Use very short timeout for test
        with pytest.raises(OpenAIVectorStoreError, match="File processing timeout"):
            await service._wait_for_file_processing("vf_123", max_wait_time=1)

    @patch('backend.services.openai_vector_store_service.OpenAI')
    @pytest.mark.asyncio
    async def test_answer_question_success(self, mock_openai_class):
        """Test successful question answering."""
        # Mock OpenAI client
        mock_client = MagicMock()
        
        # Mock chat completion response
        mock_message = MagicMock()
        mock_message.content = "The HSA contribution limits for 2024 are $4,150 for self-only coverage and $8,300 for family coverage."
        mock_message.annotations = []
        
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        
        mock_chat_completions = MagicMock()
        mock_chat_completions.create.return_value = mock_response
        mock_client.beta.chat.completions = mock_chat_completions
        
        mock_openai_class.return_value = mock_client
        
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        service.vector_store_id = "vs_test123"
        
        request = QARequest(question="What are the HSA contribution limits for 2024?")
        response = await service.answer_question(request)
        
        # Verify response structure
        assert isinstance(response, QAResponse)
        assert "$4,150" in response.answer
        assert 0.0 <= response.confidence_score <= 1.0
        assert isinstance(response.citations, list)
        assert isinstance(response.source_documents, list)
        assert response.processing_time_ms is not None
        assert response.processing_time_ms > 0
        
        # Verify OpenAI API was called correctly
        mock_chat_completions.create.assert_called_once()
        call_args = mock_chat_completions.create.call_args[1]
        
        assert call_args['model'] == "gpt-4o-mini"
        assert call_args['tools'] == [{"type": "file_search"}]
        assert call_args['tool_choice'] == "auto"
        assert call_args['temperature'] == 0.1
        assert call_args['max_tokens'] == 1500
        assert call_args['metadata'] == {"vector_store_ids": ["vs_test123"]}
        
        # Verify messages structure
        messages = call_args['messages']
        assert len(messages) == 2
        assert messages[0]['role'] == 'system'
        assert messages[1]['role'] == 'user'
        assert "What are the HSA contribution limits for 2024?" in messages[1]['content']

    @patch('backend.services.openai_vector_store_service.OpenAI')
    @pytest.mark.asyncio
    async def test_answer_question_with_context(self, mock_openai_class):
        """Test question answering with context."""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Test answer", annotations=[]))]
        mock_client.beta.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        service.vector_store_id = "vs_test123"
        
        request = QARequest(
            question="What are the limits?",
            context="I'm asking about HSA contribution limits for self-only coverage",
            application_id="app-123"
        )
        response = await service.answer_question(request)
        
        # Verify context was included in the request
        call_args = mock_client.beta.chat.completions.create.call_args[1]
        messages = call_args['messages']
        user_message = messages[1]['content']
        
        assert "Context: I'm asking about HSA contribution limits for self-only coverage" in user_message
        assert "Question: What are the limits?" in user_message

    @patch('backend.services.openai_vector_store_service.OpenAI')
    @pytest.mark.asyncio
    async def test_answer_question_no_vector_store(self, mock_openai_class):
        """Test question answering without vector store initialization."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        service.vector_store_id = None  # No vector store
        
        request = QARequest(question="Test question")
        
        with pytest.raises(OpenAIVectorStoreError, match="Vector store not initialized"):
            await service.answer_question(request)

    @patch('backend.services.openai_vector_store_service.OpenAI')
    @pytest.mark.asyncio
    async def test_answer_question_api_failure(self, mock_openai_class):
        """Test question answering with OpenAI API failure."""
        # Mock OpenAI client to raise exception
        mock_client = MagicMock()
        mock_client.beta.chat.completions.create.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_client
        
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        service.vector_store_id = "vs_test123"
        
        request = QARequest(question="Test question")
        
        with pytest.raises(OpenAIVectorStoreError, match="Question answering failed"):
            await service.answer_question(request)

    @patch('backend.services.openai_vector_store_service.OpenAI')
    @pytest.mark.asyncio
    async def test_vector_search_success(self, mock_openai_class):
        """Test successful vector search."""
        # Mock OpenAI client
        mock_client = MagicMock()
        
        # Mock search response with tool calls
        mock_tool_call = MagicMock()
        mock_tool_call.type = "file_search"
        mock_tool_call.id = "call_123"
        mock_tool_call.function.arguments = "Search result content about HSA"
        
        mock_message = MagicMock()
        mock_message.tool_calls = [mock_tool_call]
        
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        
        mock_client.beta.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        service.vector_store_id = "vs_test123"
        
        request = VectorSearchRequest(query="HSA contribution limits", k=3, threshold=0.7)
        results = await service.vector_search(request)
        
        # Verify results
        assert len(results) == 1
        assert isinstance(results[0], VectorSearchResult)
        assert results[0].chunk_id == "chunk_0"
        assert results[0].document_name == "irs.pdf"
        assert results[0].similarity_score == 0.8
        assert "Search result content about HSA" in results[0].text
        assert results[0].metadata["tool_call_id"] == "call_123"

    @patch('backend.services.openai_vector_store_service.OpenAI')
    @pytest.mark.asyncio
    async def test_vector_search_no_results(self, mock_openai_class):
        """Test vector search with no tool calls."""
        # Mock OpenAI client
        mock_client = MagicMock()
        
        mock_message = MagicMock()
        mock_message.tool_calls = None  # No tool calls
        
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        
        mock_client.beta.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        service.vector_store_id = "vs_test123"
        
        request = VectorSearchRequest(query="unknown query", k=3)
        results = await service.vector_search(request)
        
        # Should return fallback result
        assert len(results) == 1
        assert results[0].chunk_id == "fallback_chunk"
        assert results[0].similarity_score == 0.5
        assert "Search performed for: unknown query" in results[0].text

    @patch('backend.services.openai_vector_store_service.OpenAI')
    @pytest.mark.asyncio
    async def test_get_knowledge_base_stats(self, mock_openai_class):
        """Test knowledge base statistics retrieval."""
        # Mock OpenAI client
        mock_client = MagicMock()
        
        # Mock vector store details
        mock_vector_store = MagicMock()
        mock_file_counts = MagicMock()
        mock_file_counts.completed = 5
        mock_vector_store.file_counts = mock_file_counts
        mock_client.beta.vector_stores.retrieve.return_value = mock_vector_store
        
        # Mock files list
        mock_files_response = MagicMock()
        mock_files_response.data = [MagicMock(), MagicMock()]  # 2 files
        mock_client.beta.vector_stores.files.list.return_value = mock_files_response
        
        mock_openai_class.return_value = mock_client
        
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        service.vector_store_id = "vs_test123"
        
        stats = await service.get_knowledge_base_stats()
        
        # Verify stats
        assert isinstance(stats, KnowledgeBaseStats)
        assert stats.total_documents == 2
        assert stats.total_chunks == 5
        assert stats.total_embeddings == 5
        assert stats.average_chunk_size == 1000.0

    @patch('backend.services.openai_vector_store_service.OpenAI')
    @pytest.mark.asyncio
    async def test_get_knowledge_base_stats_no_vector_store(self, mock_openai_class):
        """Test knowledge base statistics with no vector store."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        service.vector_store_id = None
        
        stats = await service.get_knowledge_base_stats()
        
        # Should return empty stats
        assert stats.total_documents == 0
        assert stats.total_chunks == 0
        assert stats.total_embeddings == 0
        assert stats.average_chunk_size == 0.0

    @patch('backend.services.openai_vector_store_service.OpenAI')
    @pytest.mark.asyncio
    async def test_get_rag_metrics(self, mock_openai_class):
        """Test RAG metrics retrieval."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        
        # Set up mock metrics data
        service.query_count = 10
        service.total_response_time = 5000  # 5 seconds total
        service.confidence_scores = [0.9, 0.8, 0.7, 0.6, 0.9, 0.8, 0.7, 0.9, 0.8, 0.7]
        
        metrics = await service.get_rag_metrics()
        
        # Verify metrics
        assert isinstance(metrics, RAGMetrics)
        assert metrics.total_queries == 10
        assert metrics.average_response_time_ms == 500.0
        assert 0.7 <= metrics.average_confidence_score <= 0.9
        assert 0.8 <= metrics.citation_rate <= 1.0  # Most confidence scores > 0.5
        assert metrics.knowledge_coverage == 1.0

    @patch('backend.services.openai_vector_store_service.OpenAI')
    @pytest.mark.asyncio
    async def test_rebuild_knowledge_base(self, mock_openai_class):
        """Test knowledge base rebuild."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        
        # Mock upload_knowledge_base method
        with patch.object(service, 'upload_knowledge_base') as mock_upload:
            mock_upload.return_value = None
            
            await service.rebuild_knowledge_base()
            
            # Verify upload was called with recreate=True
            mock_upload.assert_called_once_with(recreate=True)

    @patch('backend.services.openai_vector_store_service.OpenAI')
    @pytest.mark.asyncio
    async def test_health_check(self, mock_openai_class):
        """Test service health check."""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_client.api_key = "test-key"
        
        # Mock vector store status
        mock_vector_store = MagicMock()
        mock_vector_store.status = "completed"
        mock_client.beta.vector_stores.retrieve.return_value = mock_vector_store
        
        mock_openai_class.return_value = mock_client
        
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        service.vector_store_id = "vs_test123"
        service.query_count = 5
        
        health = await service.health_check()
        
        # Verify health check results
        assert health["status"] == "healthy"
        assert health["vector_store_initialized"] is True
        assert health["vector_store_healthy"] is True
        assert health["queries_processed"] == 5
        assert health["openai_client_configured"] is True
        assert health["knowledge_base_path_exists"] is True

    def test_extract_citations_from_annotations(self):
        """Test citation extraction from OpenAI response annotations."""
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        
        # Mock annotations with file_citation
        mock_annotation = MagicMock()
        mock_annotation.file_citation = MagicMock()
        mock_annotation.text = "HSA contribution limits are $4,150 for self-only coverage as per IRS Publication 969."
        
        annotations = [mock_annotation]
        citations = service._extract_citations_from_annotations(annotations)
        
        assert len(citations) == 1
        assert isinstance(citations[0], Citation)
        assert citations[0].document_name == "irs.pdf"
        assert citations[0].relevance_score == 0.9
        assert "HSA contribution limits" in citations[0].excerpt

    def test_extract_citations_no_annotations(self):
        """Test citation extraction with no annotations."""
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        
        citations = service._extract_citations_from_annotations([])
        
        # Should return default citation
        assert len(citations) == 1
        assert citations[0].document_name == "irs.pdf"
        assert citations[0].relevance_score == 0.8
        assert "IRS Publication 969" in citations[0].excerpt

    def test_calculate_confidence(self):
        """Test confidence score calculation."""
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        
        # High quality response with citations
        citations = [
            Citation(document_name="irs.pdf", excerpt="test", relevance_score=0.9),
            Citation(document_name="irs.pdf", excerpt="test", relevance_score=0.8),
        ]
        response = "This is a detailed response about HSA contribution limits with multiple citations and comprehensive coverage of the topic. It provides specific numbers and clear explanations."
        
        confidence = service._calculate_confidence(citations, response)
        assert 0.8 <= confidence <= 1.0
        
        # Low quality response with no citations
        confidence = service._calculate_confidence([], "Short answer.")
        assert confidence == 0.3
        
        # Medium quality response
        one_citation = [Citation(document_name="irs.pdf", excerpt="test", relevance_score=0.9)]
        medium_response = "Medium length response with adequate detail."
        confidence = service._calculate_confidence(one_citation, medium_response)
        assert 0.5 <= confidence <= 0.9

    def test_calculate_processing_time(self):
        """Test processing time calculation."""
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        
        # Test with known time difference
        start_time = datetime.utcnow()
        # Simulate 100ms processing time
        import time
        time.sleep(0.1)
        
        processing_time = service._calculate_processing_time(start_time)
        
        # Should be approximately 100ms (allow some variance)
        assert 90 <= processing_time <= 200

    def test_update_metrics(self):
        """Test metrics update functionality."""
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        
        # Initial state
        assert service.query_count == 0
        assert service.total_response_time == 0.0
        assert service.confidence_scores == []
        
        # Update metrics
        service._update_metrics(0.85, 1500)
        
        assert service.query_count == 1
        assert service.total_response_time == 1500.0
        assert service.confidence_scores == [0.85]
        
        # Update again
        service._update_metrics(0.75, 1200)
        
        assert service.query_count == 2
        assert service.total_response_time == 2700.0
        assert service.confidence_scores == [0.85, 0.75]


class TestOpenAIVectorStoreServiceIntegration:
    """Integration tests for OpenAI Vector Store Service with real API patterns."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.knowledge_base_path = Path(self.temp_dir) / "knowledge_base" / "hsa"
        self.knowledge_base_path.mkdir(parents=True)
        
        # Create mock IRS PDF
        self.irs_pdf_path = self.knowledge_base_path / "irs.pdf"
        self.irs_pdf_path.write_bytes(b"Mock PDF content for IRS Publication 969")

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'})
    @patch('backend.services.openai_vector_store_service.OpenAI')
    @pytest.mark.asyncio
    async def test_complete_workflow(self, mock_openai_class):
        """Test complete workflow: create store -> upload files -> answer questions."""
        # Mock OpenAI client with full workflow
        mock_client = MagicMock()
        
        # Mock vector store creation
        mock_vector_store = MagicMock()
        mock_vector_store.id = "vs_workflow123"
        mock_client.beta.vector_stores.create.return_value = mock_vector_store
        
        # Mock file upload
        mock_uploaded_file = MagicMock()
        mock_uploaded_file.id = "file_workflow123"
        mock_client.files.create.return_value = mock_uploaded_file
        
        # Mock file attachment
        mock_vector_store_file = MagicMock()
        mock_vector_store_file.id = "vf_workflow123"
        mock_client.beta.vector_stores.files.create.return_value = mock_vector_store_file
        
        # Mock file processing completion
        mock_file_status = MagicMock()
        mock_file_status.status = "completed"
        mock_client.beta.vector_stores.files.retrieve.return_value = mock_file_status
        
        # Mock question answering
        mock_message = MagicMock()
        mock_message.content = "The HSA contribution limits for 2024 are $4,150 for self-only coverage."
        mock_message.annotations = []
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=mock_message)]
        mock_client.beta.chat.completions.create.return_value = mock_response
        
        mock_openai_class.return_value = mock_client
        
        # Execute workflow
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        
        # Step 1: Create vector store
        vector_store_id = await service.create_vector_store("hsa_knowledge_base")
        assert vector_store_id == "vs_workflow123"
        
        # Step 2: Upload knowledge base
        await service.upload_knowledge_base()
        
        # Step 3: Answer question
        request = QARequest(question="What are the HSA contribution limits?")
        response = await service.answer_question(request)
        
        # Verify end-to-end functionality
        assert isinstance(response, QAResponse)
        assert "$4,150" in response.answer
        assert response.confidence_score > 0.0
        
        # Verify all API calls were made
        mock_client.beta.vector_stores.create.assert_called_once()
        mock_client.files.create.assert_called_once()
        mock_client.beta.vector_stores.files.create.assert_called_once()
        mock_client.beta.chat.completions.create.assert_called_once()


class TestOpenAIVectorStoreServiceEdgeCases:
    """Test edge cases and error conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.knowledge_base_path = Path(self.temp_dir) / "knowledge_base" / "hsa"
        self.knowledge_base_path.mkdir(parents=True)

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_api_key(self):
        """Test initialization without API key."""
        # Should still initialize but won't work for actual API calls
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        assert service.openai_client is not None

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    @patch('backend.services.openai_vector_store_service.OpenAI')
    @pytest.mark.asyncio
    async def test_extremely_long_question(self, mock_openai_class):
        """Test handling of extremely long questions."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Response to long question", annotations=[]))]
        mock_client.beta.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        service.vector_store_id = "vs_test123"
        
        # Create very long question (over 500 chars limit in schema)
        long_question = "What are the HSA contribution limits? " * 50
        
        # Should be truncated by schema validation or handled gracefully
        request = QARequest(question=long_question[:500])  # Truncate to schema limit
        response = await service.answer_question(request)
        
        assert isinstance(response, QAResponse)
        assert response.answer == "Response to long question"

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    @patch('backend.services.openai_vector_store_service.OpenAI')
    @pytest.mark.asyncio
    async def test_empty_response_from_openai(self, mock_openai_class):
        """Test handling of empty response from OpenAI."""
        mock_client = MagicMock()
        
        # Mock empty response
        mock_message = MagicMock()
        mock_message.content = ""  # Empty content
        mock_message.annotations = []
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=mock_message)]
        mock_client.beta.chat.completions.create.return_value = mock_response
        
        mock_openai_class.return_value = mock_client
        
        service = OpenAIVectorStoreService(str(self.knowledge_base_path))
        service.vector_store_id = "vs_test123"
        
        request = QARequest(question="Test question")
        response = await service.answer_question(request)
        
        # Should handle empty response gracefully
        assert response.answer == ""
        assert isinstance(response.citations, list)
        assert len(response.citations) >= 1  # Should have default citation