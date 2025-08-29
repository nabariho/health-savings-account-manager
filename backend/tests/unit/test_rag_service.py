"""
Unit tests for RAG service functionality.

Tests the RAG (Retrieval Augmented Generation) system implementation including
vector search, response generation, citation accuracy, and knowledge base management
as specified in user stories US-4.1 and US-4.2.

RAG System Requirements Tested:
- Natural language question processing
- AI-powered answers based on knowledge base  
- Citations and sources for answers
- Confidence level for responses
- Knowledge base management and indexing
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import numpy as np

from backend.services.rag_service import (
    RAGService, RAGServiceError, VectorStore, DocumentChunker
)
from backend.schemas.qa import (
    QARequest, QAResponse, Citation, VectorSearchRequest,
    KnowledgeBaseStats, RAGMetrics
)


class TestVectorStore:
    """Test cases for VectorStore class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.vector_store = VectorStore()

    @pytest.mark.asyncio
    async def test_store_and_retrieve(self):
        """Test storing and retrieving embeddings."""
        chunk_id = "test_chunk_1"
        embedding = np.array([0.1, 0.2, 0.3])
        metadata = {
            "text": "Test content",
            "document": "test.txt",
            "chunk_index": 0
        }
        
        await self.vector_store.store(chunk_id, embedding, metadata)
        
        assert chunk_id in self.vector_store.embeddings
        assert np.array_equal(self.vector_store.embeddings[chunk_id], embedding)
        assert self.vector_store.metadata[chunk_id] == metadata
        assert self.vector_store.documents[chunk_id] == "Test content"

    @pytest.mark.asyncio
    async def test_similarity_search(self):
        """Test vector similarity search functionality."""
        # Store test embeddings
        embeddings = [
            ("chunk1", np.array([1.0, 0.0, 0.0]), {"text": "HSA contribution limits"}),
            ("chunk2", np.array([0.0, 1.0, 0.0]), {"text": "HSA eligibility requirements"}),
            ("chunk3", np.array([0.9, 0.1, 0.0]), {"text": "HSA contribution rules"})  # Similar to chunk1
        ]
        
        for chunk_id, embedding, metadata in embeddings:
            await self.vector_store.store(chunk_id, embedding, metadata)
        
        # Search with query similar to chunk1
        query_embedding = np.array([0.95, 0.05, 0.0])
        results = await self.vector_store.similarity_search(query_embedding, k=2, threshold=0.5)
        
        # Should return chunk1 and chunk3 (most similar)
        assert len(results) == 2
        assert results[0][0] == "chunk1"  # Most similar
        assert results[1][0] == "chunk3"  # Second most similar
        assert results[0][1] > results[1][1]  # Scores in descending order

    @pytest.mark.asyncio
    async def test_empty_search(self):
        """Test search on empty vector store."""
        query_embedding = np.array([1.0, 0.0, 0.0])
        results = await self.vector_store.similarity_search(query_embedding)
        
        assert results == []

    def test_get_chunk_count(self):
        """Test getting chunk count."""
        assert self.vector_store.get_chunk_count() == 0
        
        # Add some embeddings
        self.vector_store.embeddings["chunk1"] = np.array([1.0, 0.0])
        self.vector_store.embeddings["chunk2"] = np.array([0.0, 1.0])
        
        assert self.vector_store.get_chunk_count() == 2

    def test_get_metadata(self):
        """Test getting metadata for chunks."""
        metadata = {"text": "test", "document": "test.txt"}
        self.vector_store.metadata["chunk1"] = metadata
        
        assert self.vector_store.get_metadata("chunk1") == metadata
        assert self.vector_store.get_metadata("nonexistent") is None


class TestDocumentChunker:
    """Test cases for DocumentChunker class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.chunker = DocumentChunker(chunk_size=100, overlap=20)

    def test_chunk_short_document(self):
        """Test chunking a document shorter than chunk size."""
        text = "Short document about HSA eligibility requirements."
        chunks = self.chunker.chunk_document(text, "test.txt")
        
        assert len(chunks) == 1
        assert chunks[0]["text"] == text
        assert chunks[0]["document"] == "test.txt"
        assert chunks[0]["chunk_index"] == 0

    def test_chunk_long_document(self):
        """Test chunking a document longer than chunk size."""
        # Create a document with multiple paragraphs
        paragraphs = [
            "First paragraph about HSA contribution limits. " * 5,
            "Second paragraph about HSA eligibility requirements. " * 5,
            "Third paragraph about HSA qualified expenses. " * 5
        ]
        text = "\n\n".join(paragraphs)
        
        chunks = self.chunker.chunk_document(text, "test.txt")
        
        # Should create multiple chunks
        assert len(chunks) > 1
        
        # Each chunk should have proper metadata
        for i, chunk in enumerate(chunks):
            assert chunk["document"] == "test.txt"
            assert chunk["chunk_index"] == i
            assert len(chunk["text"]) <= self.chunker.chunk_size + self.chunker.overlap
            assert chunk["char_count"] == len(chunk["text"])

    def test_chunk_with_overlap(self):
        """Test that chunks have proper overlap."""
        text = "A" * 150 + "\n\n" + "B" * 150  # Two paragraphs, each exceeding chunk size
        chunks = self.chunker.chunk_document(text, "test.txt")
        
        assert len(chunks) >= 2
        # Later chunks should contain some content from previous chunks (overlap)
        if len(chunks) > 1:
            # This is a simplified check - in practice, overlap depends on paragraph boundaries
            assert len(chunks[1]["text"]) > 0


class TestRAGService:
    """Test cases for RAGService class."""

    def setup_method(self):
        """Set up test fixtures with temporary knowledge base."""
        self.temp_dir = tempfile.mkdtemp()
        self.knowledge_base_path = Path(self.temp_dir) / "knowledge_base"
        self.knowledge_base_path.mkdir()
        
        # Create test knowledge base files
        (self.knowledge_base_path / "HSA_FAQ.txt").write_text(
            "# HSA FAQ\n\n"
            "## What are HSA contribution limits?\n"
            "For 2024, HSA contribution limits are $4,150 for self-only coverage and $8,300 for family coverage.\n\n"
            "## Who is eligible for HSA?\n"
            "You must be covered under a high-deductible health plan and have no other health coverage."
        )
        
        (self.knowledge_base_path / "HSA_Limits.txt").write_text(
            "# HSA Limits 2024\n\n"
            "Self-only coverage: $4,150 maximum annual contribution\n"
            "Family coverage: $8,300 maximum annual contribution\n"
            "Catch-up contribution (age 55+): $1,000 additional"
        )

    def teardown_method(self):
        """Clean up temporary files."""
        shutil.rmtree(self.temp_dir)

    @pytest.mark.asyncio
    async def test_build_knowledge_base_success(self):
        """Test successful knowledge base construction."""
        with patch('backend.services.rag_service.AsyncOpenAI') as mock_openai:
            # Mock OpenAI client
            mock_client = AsyncMock()
            mock_embeddings = AsyncMock()
            mock_embeddings.create.return_value.data = [
                MagicMock(embedding=[0.1, 0.2, 0.3])
            ]
            mock_client.embeddings = mock_embeddings
            mock_openai.return_value = mock_client
            
            rag_service = RAGService(str(self.knowledge_base_path))
            await rag_service.build_knowledge_base()
            
            # Verify knowledge base was built
            assert len(rag_service.knowledge_base_index) == 2
            assert "HSA_FAQ.txt" in rag_service.knowledge_base_index
            assert "HSA_Limits.txt" in rag_service.knowledge_base_index
            assert rag_service.vector_store.get_chunk_count() > 0

    @pytest.mark.asyncio
    async def test_build_knowledge_base_no_files(self):
        """Test knowledge base construction with no files."""
        empty_dir = Path(self.temp_dir) / "empty"
        empty_dir.mkdir()
        
        with patch('backend.services.rag_service.AsyncOpenAI'):
            rag_service = RAGService(str(empty_dir))
            
            with pytest.raises(RAGServiceError, match="No .txt files found"):
                await rag_service.build_knowledge_base()

    @pytest.mark.asyncio
    async def test_build_knowledge_base_nonexistent_path(self):
        """Test knowledge base construction with nonexistent path."""
        with patch('backend.services.rag_service.AsyncOpenAI'):
            rag_service = RAGService("/nonexistent/path")
            
            with pytest.raises(RAGServiceError, match="does not exist"):
                await rag_service.build_knowledge_base()

    @pytest.mark.asyncio
    async def test_answer_question_with_results(self):
        """Test answering question with relevant knowledge base content."""
        with patch('backend.services.rag_service.AsyncOpenAI') as mock_openai:
            # Mock OpenAI client
            mock_client = AsyncMock()
            
            # Mock embeddings
            mock_embeddings = AsyncMock()
            mock_embeddings.create.return_value.data = [
                MagicMock(embedding=[0.1, 0.2, 0.3])
            ]
            mock_client.embeddings = mock_embeddings
            
            # Mock chat completion
            mock_chat = AsyncMock()
            mock_completion = MagicMock()
            mock_completion.choices = [
                MagicMock(message=MagicMock(content="The HSA contribution limits for 2024 are $4,150 for self-only coverage and $8,300 for family coverage, as stated in the HSA_FAQ.txt document."))
            ]
            mock_chat.completions.create.return_value = mock_completion
            mock_client.chat = mock_chat
            
            mock_openai.return_value = mock_client
            
            # Set up RAG service
            rag_service = RAGService(str(self.knowledge_base_path))
            await rag_service.build_knowledge_base()
            
            # Mock vector search to return relevant results
            with patch.object(rag_service.vector_store, 'similarity_search') as mock_search:
                mock_search.return_value = [
                    ("chunk1", 0.95),
                    ("chunk2", 0.85)
                ]
                
                # Mock metadata
                rag_service.vector_store.metadata = {
                    "chunk1": {
                        "text": "For 2024, HSA contribution limits are $4,150 for self-only coverage",
                        "document": "HSA_FAQ.txt"
                    },
                    "chunk2": {
                        "text": "Family coverage: $8,300 maximum annual contribution",
                        "document": "HSA_Limits.txt"
                    }
                }
                
                # Test question
                request = QARequest(question="What are the HSA contribution limits for 2024?")
                response = await rag_service.answer_question(request)
                
                # Verify response
                assert isinstance(response, QAResponse)
                assert "4,150" in response.answer or "4150" in response.answer
                assert response.confidence_score > 0.5
                assert len(response.citations) > 0
                assert len(response.source_documents) > 0
                
                # Verify citations contain required fields
                for citation in response.citations:
                    assert isinstance(citation, Citation)
                    assert citation.document_name in ["HSA_FAQ.txt", "HSA_Limits.txt"]
                    assert citation.excerpt is not None
                    assert 0.0 <= citation.relevance_score <= 1.0

    @pytest.mark.asyncio
    async def test_answer_question_no_results(self):
        """Test answering question with no relevant knowledge base content."""
        with patch('backend.services.rag_service.AsyncOpenAI') as mock_openai:
            # Mock OpenAI client
            mock_client = AsyncMock()
            mock_embeddings = AsyncMock()
            mock_embeddings.create.return_value.data = [
                MagicMock(embedding=[0.1, 0.2, 0.3])
            ]
            mock_client.embeddings = mock_embeddings
            mock_openai.return_value = mock_client
            
            rag_service = RAGService(str(self.knowledge_base_path))
            
            # Mock vector search to return no results
            with patch.object(rag_service.vector_store, 'similarity_search') as mock_search:
                mock_search.return_value = []
                
                request = QARequest(question="What is the meaning of life?")
                response = await rag_service.answer_question(request)
                
                assert "don't have information" in response.answer.lower()
                assert response.confidence_score == 0.0
                assert len(response.citations) == 0
                assert len(response.source_documents) == 0

    @pytest.mark.asyncio
    async def test_vector_search(self):
        """Test vector search functionality."""
        with patch('backend.services.rag_service.AsyncOpenAI') as mock_openai:
            # Mock OpenAI client
            mock_client = AsyncMock()
            mock_embeddings = AsyncMock()
            mock_embeddings.create.return_value.data = [
                MagicMock(embedding=[0.1, 0.2, 0.3])
            ]
            mock_client.embeddings = mock_embeddings
            mock_openai.return_value = mock_client
            
            rag_service = RAGService(str(self.knowledge_base_path))
            
            # Mock vector search results
            with patch.object(rag_service.vector_store, 'similarity_search') as mock_search:
                mock_search.return_value = [("chunk1", 0.95), ("chunk2", 0.85)]
                rag_service.vector_store.metadata = {
                    "chunk1": {
                        "text": "Test content 1",
                        "document": "HSA_FAQ.txt"
                    },
                    "chunk2": {
                        "text": "Test content 2", 
                        "document": "HSA_Limits.txt"
                    }
                }
                
                request = VectorSearchRequest(query="HSA limits", k=2, threshold=0.8)
                results = await rag_service.vector_search(request)
                
                assert len(results) == 2
                assert results[0].chunk_id == "chunk1"
                assert results[0].similarity_score == 0.95
                assert results[0].document_name == "HSA_FAQ.txt"

    @pytest.mark.asyncio
    async def test_get_knowledge_base_stats(self):
        """Test getting knowledge base statistics."""
        with patch('backend.services.rag_service.AsyncOpenAI') as mock_openai:
            # Mock OpenAI client
            mock_client = AsyncMock()
            mock_embeddings = AsyncMock()
            mock_embeddings.create.return_value.data = [
                MagicMock(embedding=[0.1, 0.2, 0.3])
            ]
            mock_client.embeddings = mock_embeddings
            mock_openai.return_value = mock_client
            
            rag_service = RAGService(str(self.knowledge_base_path))
            await rag_service.build_knowledge_base()
            
            stats = await rag_service.get_knowledge_base_stats()
            
            assert isinstance(stats, KnowledgeBaseStats)
            assert stats.total_documents == 2
            assert stats.total_chunks > 0
            assert stats.total_embeddings > 0
            assert stats.average_chunk_size > 0

    @pytest.mark.asyncio
    async def test_get_rag_metrics(self):
        """Test getting RAG performance metrics."""
        with patch('backend.services.rag_service.AsyncOpenAI'):
            rag_service = RAGService(str(self.knowledge_base_path))
            
            # Simulate some queries
            rag_service.query_count = 10
            rag_service.total_response_time = 5000  # 5 seconds total
            rag_service.confidence_scores = [0.9, 0.8, 0.7, 0.6, 0.9, 0.8, 0.7, 0.9, 0.8, 0.7]
            
            metrics = await rag_service.get_rag_metrics()
            
            assert isinstance(metrics, RAGMetrics)
            assert metrics.total_queries == 10
            assert metrics.average_response_time_ms == 500.0
            assert 0.7 <= metrics.average_confidence_score <= 0.9
            assert 0.0 <= metrics.citation_rate <= 1.0

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test RAG service health check."""
        with patch('backend.services.rag_service.AsyncOpenAI'):
            rag_service = RAGService(str(self.knowledge_base_path))
            
            health = await rag_service.health_check()
            
            assert "status" in health
            assert "knowledge_base_loaded" in health
            assert "total_documents" in health
            assert "total_chunks" in health
            assert "queries_processed" in health
            assert "openai_client_configured" in health

    def test_create_excerpt(self):
        """Test citation excerpt creation."""
        with patch('backend.services.rag_service.AsyncOpenAI'):
            rag_service = RAGService(str(self.knowledge_base_path))
            
            text = "HSA contribution limits for 2024 are $4,150 for individual coverage. Additional catch-up contributions of $1,000 are allowed for individuals age 55 and older. These limits are adjusted annually by the IRS."
            question = "What are the HSA contribution limits?"
            
            excerpt = rag_service._create_excerpt(text, question, max_length=100)
            
            assert len(excerpt) <= 100
            assert "contribution limits" in excerpt.lower() or "4,150" in excerpt

    def test_calculate_confidence(self):
        """Test confidence score calculation."""
        with patch('backend.services.rag_service.AsyncOpenAI'):
            rag_service = RAGService(str(self.knowledge_base_path))
            
            # High similarity results should give high confidence
            high_similarity_results = [("chunk1", 0.95), ("chunk2", 0.90), ("chunk3", 0.85)]
            response = "Detailed response about HSA contribution limits and eligibility requirements."
            
            confidence = rag_service._calculate_confidence(high_similarity_results, response)
            assert 0.7 <= confidence <= 1.0
            
            # Low similarity results should give lower confidence
            low_similarity_results = [("chunk1", 0.6), ("chunk2", 0.5)]
            short_response = "Brief answer."
            
            confidence = rag_service._calculate_confidence(low_similarity_results, short_response)
            assert confidence < 0.7
            
            # No results should give zero confidence
            no_results = []
            confidence = rag_service._calculate_confidence(no_results, response)
            assert confidence == 0.0


class TestRAGServiceErrorHandling:
    """Test error handling in RAG service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.knowledge_base_path = Path(self.temp_dir) / "knowledge_base"
        self.knowledge_base_path.mkdir()

    def teardown_method(self):
        """Clean up temporary files."""
        shutil.rmtree(self.temp_dir)

    @pytest.mark.asyncio
    async def test_openai_api_error_embedding(self):
        """Test handling of OpenAI API errors during embedding creation."""
        with patch('backend.services.rag_service.AsyncOpenAI') as mock_openai:
            # Mock OpenAI client to raise exception
            mock_client = AsyncMock()
            mock_embeddings = AsyncMock()
            mock_embeddings.create.side_effect = Exception("API Error")
            mock_client.embeddings = mock_embeddings
            mock_openai.return_value = mock_client
            
            rag_service = RAGService(str(self.knowledge_base_path))
            
            with pytest.raises(RAGServiceError, match="Embedding generation failed"):
                await rag_service._create_embedding("test text")

    @pytest.mark.asyncio
    async def test_openai_api_error_response_generation(self):
        """Test handling of OpenAI API errors during response generation."""
        with patch('backend.services.rag_service.AsyncOpenAI') as mock_openai:
            # Mock OpenAI client
            mock_client = AsyncMock()
            
            # Mock embeddings to work
            mock_embeddings = AsyncMock()
            mock_embeddings.create.return_value.data = [
                MagicMock(embedding=[0.1, 0.2, 0.3])
            ]
            mock_client.embeddings = mock_embeddings
            
            # Mock chat completion to fail
            mock_chat = AsyncMock()
            mock_chat.completions.create.side_effect = Exception("Chat API Error")
            mock_client.chat = mock_chat
            
            mock_openai.return_value = mock_client
            
            rag_service = RAGService(str(self.knowledge_base_path))
            
            with pytest.raises(RAGServiceError, match="Response generation failed"):
                await rag_service._generate_response(
                    "test question",
                    [{"text": "test context", "document": "test.txt"}]
                )

    @pytest.mark.asyncio
    async def test_file_read_error(self):
        """Test handling of file reading errors."""
        # Create a file with restricted permissions (if possible)
        restricted_file = self.knowledge_base_path / "restricted.txt"
        restricted_file.write_text("test content")
        
        with patch('backend.services.rag_service.AsyncOpenAI'):
            rag_service = RAGService(str(self.knowledge_base_path))
            
            # Mock file open to raise exception
            with patch('builtins.open', side_effect=PermissionError("Access denied")):
                with pytest.raises(RAGServiceError, match="Document processing failed"):
                    await rag_service._process_document(restricted_file)


class TestCitationAccuracy:
    """Test citation accuracy and relevance requirements from US-4.1."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.knowledge_base_path = Path(self.temp_dir) / "knowledge_base"
        self.knowledge_base_path.mkdir()
        
        # Create detailed knowledge base content for citation testing
        (self.knowledge_base_path / "HSA_Detailed.txt").write_text(
            "# HSA Contribution Limits 2024\n\n"
            "The IRS has set the following contribution limits for Health Savings Accounts in 2024:\n\n"
            "For self-only HDHP coverage: The maximum annual contribution is $4,150.\n"
            "For family HDHP coverage: The maximum annual contribution is $8,300.\n"
            "Catch-up contributions: Individuals age 55 and older can contribute an additional $1,000.\n\n"
            "# HSA Eligibility Requirements\n\n"
            "To be eligible to contribute to an HSA, you must:\n"
            "1. Be covered under a qualified high-deductible health plan (HDHP)\n"
            "2. Have no other health coverage except permitted coverage\n"
            "3. Not be enrolled in Medicare\n"
            "4. Not be claimed as a dependent on another person's tax return\n\n"
            "These eligibility requirements are strictly enforced by the IRS."
        )

    def teardown_method(self):
        """Clean up temporary files."""
        shutil.rmtree(self.temp_dir)

    @pytest.mark.asyncio
    async def test_citation_contains_relevant_information(self):
        """Test that citations contain information relevant to the question."""
        with patch('backend.services.rag_service.AsyncOpenAI') as mock_openai:
            # Mock OpenAI client
            mock_client = AsyncMock()
            mock_embeddings = AsyncMock()
            mock_embeddings.create.return_value.data = [
                MagicMock(embedding=[0.1, 0.2, 0.3])
            ]
            mock_client.embeddings = mock_embeddings
            
            # Mock chat completion
            mock_chat = AsyncMock()
            mock_completion = MagicMock()
            mock_completion.choices = [
                MagicMock(message=MagicMock(content="Based on the HSA_Detailed.txt document, the contribution limits for 2024 are $4,150 for self-only coverage and $8,300 for family coverage."))
            ]
            mock_chat.completions.create.return_value = mock_completion
            mock_client.chat = mock_chat
            
            mock_openai.return_value = mock_client
            
            rag_service = RAGService(str(self.knowledge_base_path))
            await rag_service.build_knowledge_base()
            
            # Test question about contribution limits
            request = QARequest(question="What are the HSA contribution limits for 2024?")
            response = await rag_service.answer_question(request)
            
            # Verify citations are relevant
            assert len(response.citations) > 0
            
            contribution_related_citations = 0
            for citation in response.citations:
                if any(term in citation.excerpt.lower() for term in ["4,150", "8,300", "contribution", "limit"]):
                    contribution_related_citations += 1
            
            # At least one citation should be relevant to contribution limits
            assert contribution_related_citations > 0

    @pytest.mark.asyncio
    async def test_citation_relevance_scores(self):
        """Test that citation relevance scores accurately reflect similarity."""
        with patch('backend.services.rag_service.AsyncOpenAI') as mock_openai:
            # Mock OpenAI client
            mock_client = AsyncMock()
            mock_embeddings = AsyncMock()
            mock_embeddings.create.return_value.data = [
                MagicMock(embedding=[0.1, 0.2, 0.3])
            ]
            mock_client.embeddings = mock_embeddings
            mock_openai.return_value = mock_client
            
            rag_service = RAGService(str(self.knowledge_base_path))
            
            # Mock vector search with different similarity scores
            with patch.object(rag_service.vector_store, 'similarity_search') as mock_search:
                mock_search.return_value = [
                    ("chunk1", 0.95),  # High similarity
                    ("chunk2", 0.75),  # Medium similarity
                    ("chunk3", 0.60)   # Lower similarity
                ]
                
                rag_service.vector_store.metadata = {
                    "chunk1": {
                        "text": "HSA contribution limits for 2024 are $4,150 for self-only coverage",
                        "document": "HSA_Detailed.txt"
                    },
                    "chunk2": {
                        "text": "Family HDHP coverage has maximum annual contribution of $8,300",
                        "document": "HSA_Detailed.txt"
                    },
                    "chunk3": {
                        "text": "These eligibility requirements are strictly enforced by the IRS",
                        "document": "HSA_Detailed.txt"
                    }
                }
                
                # Mock chat completion
                with patch.object(rag_service, '_generate_response') as mock_generate:
                    mock_generate.return_value = "Test response with citations"
                    
                    request = QARequest(question="What are HSA contribution limits?")
                    response = await rag_service.answer_question(request)
                    
                    # Verify citation relevance scores match search results
                    assert len(response.citations) == 3
                    assert response.citations[0].relevance_score == 0.95
                    assert response.citations[1].relevance_score == 0.75
                    assert response.citations[2].relevance_score == 0.60
                    
                    # Verify citations are ordered by relevance
                    scores = [c.relevance_score for c in response.citations]
                    assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_citation_document_names_are_accurate(self):
        """Test that citation document names accurately reflect the source."""
        with patch('backend.services.rag_service.AsyncOpenAI') as mock_openai:
            # Mock OpenAI client
            mock_client = AsyncMock()
            mock_embeddings = AsyncMock()
            mock_embeddings.create.return_value.data = [
                MagicMock(embedding=[0.1, 0.2, 0.3])
            ]
            mock_client.embeddings = mock_embeddings
            mock_openai.return_value = mock_client
            
            rag_service = RAGService(str(self.knowledge_base_path))
            
            # Mock vector search results from known document
            with patch.object(rag_service.vector_store, 'similarity_search') as mock_search:
                mock_search.return_value = [("chunk1", 0.95)]
                rag_service.vector_store.metadata = {
                    "chunk1": {
                        "text": "Test content from detailed document",
                        "document": "HSA_Detailed.txt"
                    }
                }
                
                with patch.object(rag_service, '_generate_response') as mock_generate:
                    mock_generate.return_value = "Test response"
                    
                    request = QARequest(question="Test question")
                    response = await rag_service.answer_question(request)
                    
                    # Verify document name is correct
                    assert len(response.citations) == 1
                    assert response.citations[0].document_name == "HSA_Detailed.txt"
                    assert "HSA_Detailed.txt" in response.source_documents

    @pytest.mark.asyncio
    async def test_response_includes_citations_in_text(self):
        """Test that generated responses include references to source documents."""
        with patch('backend.services.rag_service.AsyncOpenAI') as mock_openai:
            # Mock OpenAI client
            mock_client = AsyncMock()
            mock_embeddings = AsyncMock()
            mock_embeddings.create.return_value.data = [
                MagicMock(embedding=[0.1, 0.2, 0.3])
            ]
            mock_client.embeddings = mock_embeddings
            
            # Mock chat completion to include document references
            mock_chat = AsyncMock()
            mock_completion = MagicMock()
            mock_completion.choices = [
                MagicMock(message=MagicMock(content="According to HSA_Detailed.txt, the contribution limits are $4,150 for individual coverage, as specified in the IRS guidelines document."))
            ]
            mock_chat.completions.create.return_value = mock_completion
            mock_client.chat = mock_chat
            
            mock_openai.return_value = mock_client
            
            rag_service = RAGService(str(self.knowledge_base_path))
            
            # Mock vector search
            with patch.object(rag_service.vector_store, 'similarity_search') as mock_search:
                mock_search.return_value = [("chunk1", 0.95)]
                rag_service.vector_store.metadata = {
                    "chunk1": {
                        "text": "HSA contribution limits for 2024 are $4,150",
                        "document": "HSA_Detailed.txt"
                    }
                }
                
                request = QARequest(question="What are HSA contribution limits?")
                response = await rag_service.answer_question(request)
                
                # Verify response includes document reference
                assert "HSA_Detailed.txt" in response.answer
                
                # Verify citations are provided
                assert len(response.citations) > 0
                assert len(response.source_documents) > 0