"""
RAG System Performance and Accuracy Tests.

This module provides comprehensive tests for RAG (Retrieval Augmented Generation)
system performance, accuracy, and quality metrics as specified in user stories
US-4.1 and US-4.2.
"""

import pytest
import asyncio
import tempfile
import shutil
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import numpy as np

from backend.services.rag_service import RAGService, RAGServiceError, VectorStore
from backend.schemas.hsa_assistant import QARequest, QAResponse, VectorSearchRequest


class TestRAGPerformance:
    """Performance tests for RAG system."""

    def setup_method(self):
        """Set up test fixtures with sample knowledge base."""
        self.temp_dir = tempfile.mkdtemp()
        self.knowledge_base_path = Path(self.temp_dir) / "knowledge_base"
        self.knowledge_base_path.mkdir()
        
        # Create comprehensive test knowledge base
        self._create_test_knowledge_base()

    def teardown_method(self):
        """Clean up temporary files."""
        shutil.rmtree(self.temp_dir)

    def _create_test_knowledge_base(self):
        """Create test knowledge base with various HSA documents."""
        documents = {
            "HSA_Contribution_Limits.txt": """
# HSA Contribution Limits 2024

## Annual Contribution Limits
For tax year 2024, the IRS has set the following HSA contribution limits:

### Self-Only HDHP Coverage
- Maximum annual contribution: $4,150
- This applies to individuals with self-only coverage under a qualified high-deductible health plan

### Family HDHP Coverage  
- Maximum annual contribution: $8,300
- This applies to individuals with family coverage under a qualified high-deductible health plan

### Catch-Up Contributions
- Additional contribution for individuals age 55 and older: $1,000
- This catch-up contribution is available regardless of coverage type
- Must be made by the individual who is 55 or older, not their spouse

## Important Notes
- Contribution limits are subject to annual adjustment by the IRS
- Contributions can be made by the individual, employer, or both
- Total contributions from all sources cannot exceed the annual limit
            """,
            
            "HSA_Eligibility_Requirements.txt": """
# HSA Eligibility Requirements

## Primary Eligibility Criteria
To be eligible to contribute to an HSA, you must meet ALL of the following requirements:

### 1. High-Deductible Health Plan (HDHP) Coverage
- You must be covered under a qualified HDHP on the first day of the month
- The HDHP must meet minimum deductible and maximum out-of-pocket requirements

### 2. No Other Health Coverage
- You cannot have any other health coverage that is not an HDHP
- Certain limited coverage is permitted (dental, vision, long-term care)

### 3. Not Enrolled in Medicare
- You cannot be enrolled in any part of Medicare
- This includes Medicare Part A, B, C, or D

### 4. Not Claimed as Dependent
- You cannot be claimed as a dependent on another person's tax return

## HDHP Requirements for 2024
### Self-Only Coverage
- Minimum annual deductible: $1,600
- Maximum annual out-of-pocket: $8,050

### Family Coverage
- Minimum annual deductible: $3,200
- Maximum annual out-of-pocket: $16,100

## Testing Periods
- Last-month rule: If eligible on December 1st, can contribute for full year
- Testing period: Must remain eligible for 12 months following
            """,
            
            "HSA_Qualified_Expenses.txt": """
# HSA Qualified Medical Expenses

## What Qualifies
HSA funds can be used tax-free for qualified medical expenses as defined by IRS Publication 502.

### Medical Care
- Doctor visits and consultations
- Hospital services and procedures
- Prescription medications
- Medical equipment and supplies
- Diagnostic tests and laboratory fees

### Dental Care
- Routine dental checkups and cleanings
- Dental procedures and treatments
- Orthodontic treatment
- Dental appliances and prosthetics

### Vision Care
- Eye examinations
- Prescription glasses and contact lenses
- Vision correction surgery (LASIK, etc.)
- Reading glasses (prescription only)

### Preventive Care
- Annual physical examinations
- Immunizations and vaccinations
- Screening services (mammograms, colonoscopies)
- Preventive care as defined by IRS

## What Does NOT Qualify
- Cosmetic procedures (unless medically necessary)
- General health and wellness items
- Vitamins and supplements (unless prescribed)
- Health club memberships
- Non-prescription medications (with some exceptions)

## Special Considerations
- After age 65: HSA funds can be used for non-medical expenses (subject to income tax)
- Documentation required: Keep receipts and documentation for all HSA expenses
            """,
            
            "HSA_Account_Management.txt": """
# HSA Account Management

## Opening an HSA
### Requirements
- Must be eligible for HSA contributions
- Can open through banks, credit unions, or other qualified trustees
- Only one HSA per individual (though multiple accounts allowed)

### Account Features
- Account holder owns the HSA
- Funds roll over year to year (no "use it or lose it")
- Portable - stays with you if you change jobs or health plans

## Contributing to Your HSA
### Who Can Contribute
- Account holder
- Employer (through payroll deduction or direct contribution)
- Family members or others (considered taxable gift to account holder)

### Timing of Contributions
- Contributions for tax year can be made through tax filing deadline
- Typically April 15th of following year
- Monthly contribution limits apply if not eligible for full year

## Using HSA Funds
### Payment Methods
- HSA debit card
- Online bill pay
- Reimbursement (pay out-of-pocket, then reimburse yourself)
- Mobile apps and digital wallets

### Record Keeping
- Keep all receipts and documentation
- HSA provider may require substantiation
- IRS may audit HSA transactions

## Investment Options
- Many HSA providers offer investment options
- Minimum balance requirements may apply
- Investment gains are tax-free if used for qualified expenses
- Consider investment options for long-term healthcare planning
            """
        }
        
        for filename, content in documents.items():
            (self.knowledge_base_path / filename).write_text(content.strip())

    @pytest.mark.asyncio
    async def test_knowledge_base_build_performance(self):
        """Test knowledge base construction performance."""
        with patch('backend.services.rag_service.AsyncOpenAI') as mock_openai:
            # Mock OpenAI client
            mock_client = AsyncMock()
            mock_embeddings = AsyncMock()
            # Simulate realistic embedding response
            mock_embeddings.create.return_value.data = [
                MagicMock(embedding=np.random.rand(1536).tolist())  # text-embedding-3-large dimension
            ]
            mock_client.embeddings = mock_embeddings
            mock_openai.return_value = mock_client
            
            rag_service = RAGService(str(self.knowledge_base_path))
            
            # Measure build time
            start_time = time.time()
            await rag_service.build_knowledge_base()
            build_time = time.time() - start_time
            
            # Performance assertions
            assert build_time < 30.0  # Should build in under 30 seconds
            assert len(rag_service.knowledge_base_index) == 4  # All documents loaded
            assert rag_service.vector_store.get_chunk_count() > 0  # Chunks created
            
            # Verify reasonable chunking
            chunk_count = rag_service.vector_store.get_chunk_count()
            assert 10 <= chunk_count <= 100  # Reasonable number of chunks for test data

    @pytest.mark.asyncio
    async def test_query_response_time_performance(self):
        """Test query response time performance."""
        with patch('backend.services.rag_service.AsyncOpenAI') as mock_openai:
            # Mock OpenAI client with realistic delays
            mock_client = AsyncMock()
            
            # Mock embedding creation (fast)
            mock_embeddings = AsyncMock()
            mock_embeddings.create.return_value.data = [
                MagicMock(embedding=np.random.rand(1536).tolist())
            ]
            mock_client.embeddings = mock_embeddings
            
            # Mock chat completion (slower, more realistic)
            mock_chat = AsyncMock()
            async def mock_chat_create(*args, **kwargs):
                await asyncio.sleep(0.1)  # Simulate 100ms API call
                mock_completion = MagicMock()
                mock_completion.choices = [
                    MagicMock(message=MagicMock(content="The HSA contribution limits for 2024 are $4,150 for self-only coverage and $8,300 for family coverage."))
                ]
                return mock_completion
            mock_chat.completions.create = mock_chat_create
            mock_client.chat = mock_chat
            
            mock_openai.return_value = mock_client
            
            rag_service = RAGService(str(self.knowledge_base_path))
            await rag_service.build_knowledge_base()
            
            # Mock vector search to return results quickly
            with patch.object(rag_service.vector_store, 'similarity_search') as mock_search:
                mock_search.return_value = [
                    ("chunk1", 0.95),
                    ("chunk2", 0.90)
                ]
                
                rag_service.vector_store.metadata = {
                    "chunk1": {
                        "text": "HSA contribution limits for 2024 are $4,150 for self-only coverage",
                        "document": "HSA_Contribution_Limits.txt"
                    },
                    "chunk2": {
                        "text": "Family coverage maximum is $8,300 per year",
                        "document": "HSA_Contribution_Limits.txt"
                    }
                }
                
                # Test multiple queries for performance consistency
                query_times = []
                test_questions = [
                    "What are the HSA contribution limits?",
                    "Who is eligible for an HSA?",
                    "What are qualified medical expenses?",
                    "How do I manage my HSA account?",
                ]
                
                for question in test_questions:
                    request = QARequest(question=question)
                    
                    start_time = time.time()
                    response = await rag_service.answer_question(request)
                    query_time = time.time() - start_time
                    query_times.append(query_time)
                    
                    # Verify response quality
                    assert isinstance(response, QAResponse)
                    assert response.processing_time_ms > 0
                
                # Performance assertions
                avg_query_time = sum(query_times) / len(query_times)
                max_query_time = max(query_times)
                
                assert avg_query_time < 2.0  # Average under 2 seconds
                assert max_query_time < 5.0   # No query over 5 seconds
                assert all(t > 0.05 for t in query_times)  # Sanity check - not too fast

    @pytest.mark.asyncio
    async def test_vector_search_accuracy(self):
        """Test vector search accuracy and relevance."""
        with patch('backend.services.rag_service.AsyncOpenAI') as mock_openai:
            # Mock OpenAI client
            mock_client = AsyncMock()
            
            # Create deterministic embeddings for testing
            def create_mock_embedding(text):
                # Simple embedding based on text content for testing
                words = text.lower().split()
                embedding = np.zeros(100)  # Smaller embedding for testing
                
                # Create pseudo-embeddings based on key terms
                key_terms = {
                    'contribution': 10, 'limit': 11, 'hsa': 12, '4150': 13, '8300': 14,
                    'eligible': 20, 'eligibility': 21, 'hdhp': 22, 'deductible': 23,
                    'qualified': 30, 'medical': 31, 'expense': 32, 'prescription': 33,
                    'account': 40, 'management': 41, 'investment': 42, 'rollover': 43
                }
                
                for word in words:
                    if word in key_terms:
                        embedding[key_terms[word]] = 1.0
                
                # Add some noise
                embedding += np.random.normal(0, 0.1, 100)
                return embedding.tolist()
            
            mock_embeddings = AsyncMock()
            mock_embeddings.create.side_effect = lambda model, input, **kwargs: MagicMock(
                data=[MagicMock(embedding=create_mock_embedding(input))]
            )
            mock_client.embeddings = mock_embeddings
            mock_openai.return_value = mock_client
            
            rag_service = RAGService(str(self.knowledge_base_path))
            await rag_service.build_knowledge_base()
            
            # Test vector search accuracy
            test_cases = [
                {
                    "query": "HSA contribution limits 2024",
                    "expected_docs": ["HSA_Contribution_Limits.txt"],
                    "min_similarity": 0.5
                },
                {
                    "query": "HSA eligibility requirements HDHP",
                    "expected_docs": ["HSA_Eligibility_Requirements.txt"],
                    "min_similarity": 0.4
                },
                {
                    "query": "qualified medical expenses prescription",
                    "expected_docs": ["HSA_Qualified_Expenses.txt"],
                    "min_similarity": 0.4
                },
                {
                    "query": "HSA account management investment options",
                    "expected_docs": ["HSA_Account_Management.txt"],
                    "min_similarity": 0.4
                }
            ]
            
            for test_case in test_cases:
                request = VectorSearchRequest(
                    query=test_case["query"],
                    k=5,
                    threshold=0.3
                )
                
                results = await rag_service.vector_search(request)
                
                # Verify we got results
                assert len(results) > 0
                
                # Verify similarity scores are reasonable
                for result in results:
                    assert result.similarity_score >= test_case["min_similarity"]
                
                # Verify expected documents are in results
                result_docs = [r.document_name for r in results]
                for expected_doc in test_case["expected_docs"]:
                    assert expected_doc in result_docs

    @pytest.mark.asyncio
    async def test_rag_system_accuracy_metrics(self):
        """Test RAG system accuracy through question-answer pairs."""
        with patch('backend.services.rag_service.AsyncOpenAI') as mock_openai:
            # Mock OpenAI with realistic responses
            mock_client = AsyncMock()
            mock_embeddings = AsyncMock()
            mock_embeddings.create.return_value.data = [
                MagicMock(embedding=np.random.rand(100).tolist())
            ]
            mock_client.embeddings = mock_embeddings
            
            # Mock chat with contextual responses
            mock_chat = AsyncMock()
            def mock_chat_create(model, messages, **kwargs):
                user_message = messages[-1]['content'].lower()
                
                if 'contribution limit' in user_message or '4150' in user_message or '8300' in user_message:
                    content = "Based on the HSA documentation, the contribution limits for 2024 are $4,150 for self-only coverage and $8,300 for family coverage, as specified in HSA_Contribution_Limits.txt."
                elif 'eligib' in user_message or 'hdhp' in user_message:
                    content = "According to HSA_Eligibility_Requirements.txt, to be eligible for HSA you must have HDHP coverage, no other health coverage, not be on Medicare, and not be claimed as a dependent."
                elif 'qualified expense' in user_message or 'medical expense' in user_message:
                    content = "Per HSA_Qualified_Expenses.txt, qualified medical expenses include doctor visits, prescriptions, dental care, vision care, and preventive care as defined by IRS Publication 502."
                elif 'account management' in user_message or 'investment' in user_message:
                    content = "HSA_Account_Management.txt explains that HSAs can be opened through banks or trustees, funds roll over annually, and many providers offer investment options for long-term planning."
                else:
                    content = "I don't have specific information about that topic in my HSA knowledge base."
                
                return MagicMock(choices=[MagicMock(message=MagicMock(content=content))])
            
            mock_chat.completions.create.side_effect = mock_chat_create
            mock_client.chat = mock_chat
            mock_openai.return_value = mock_client
            
            rag_service = RAGService(str(self.knowledge_base_path))
            await rag_service.build_knowledge_base()
            
            # Test question-answer accuracy
            test_qa_pairs = [
                {
                    "question": "What are the HSA contribution limits for 2024?",
                    "expected_keywords": ["4,150", "4150", "8,300", "8300", "self-only", "family"],
                    "min_confidence": 0.7
                },
                {
                    "question": "What are the HSA eligibility requirements?",
                    "expected_keywords": ["HDHP", "high-deductible", "Medicare", "dependent"],
                    "min_confidence": 0.6
                },
                {
                    "question": "What are qualified medical expenses for HSA?",
                    "expected_keywords": ["doctor", "prescription", "dental", "vision", "medical"],
                    "min_confidence": 0.6
                },
                {
                    "question": "How do I manage my HSA account?",
                    "expected_keywords": ["bank", "trustee", "rollover", "investment", "portable"],
                    "min_confidence": 0.5
                },
                {
                    "question": "What is the weather today?",  # Non-HSA question
                    "expected_keywords": ["don't have", "information", "knowledge base"],
                    "max_confidence": 0.3
                }
            ]
            
            accuracy_scores = []
            
            for qa_pair in test_qa_pairs:
                request = QARequest(question=qa_pair["question"])
                
                # Mock vector search based on question content
                relevant_chunks = []
                if "contribution limit" in qa_pair["question"].lower():
                    relevant_chunks = [("contrib_chunk", 0.9), ("limit_chunk", 0.85)]
                elif "eligib" in qa_pair["question"].lower():
                    relevant_chunks = [("elig_chunk", 0.88), ("hdhp_chunk", 0.82)]
                elif "qualified expense" in qa_pair["question"].lower() or "medical expense" in qa_pair["question"].lower():
                    relevant_chunks = [("expense_chunk", 0.87), ("medical_chunk", 0.80)]
                elif "account management" in qa_pair["question"].lower():
                    relevant_chunks = [("account_chunk", 0.85), ("mgmt_chunk", 0.78)]
                else:
                    relevant_chunks = []  # No relevant chunks for non-HSA questions
                
                with patch.object(rag_service.vector_store, 'similarity_search') as mock_search:
                    mock_search.return_value = relevant_chunks
                    
                    # Mock metadata based on chunks
                    metadata = {}
                    for chunk_id, _ in relevant_chunks:
                        if "contrib" in chunk_id or "limit" in chunk_id:
                            metadata[chunk_id] = {
                                "text": "HSA contribution limits for 2024 are $4,150 for self-only coverage and $8,300 for family coverage",
                                "document": "HSA_Contribution_Limits.txt"
                            }
                        elif "elig" in chunk_id or "hdhp" in chunk_id:
                            metadata[chunk_id] = {
                                "text": "To be eligible for HSA you must have HDHP coverage and no other health coverage",
                                "document": "HSA_Eligibility_Requirements.txt"
                            }
                        elif "expense" in chunk_id or "medical" in chunk_id:
                            metadata[chunk_id] = {
                                "text": "Qualified medical expenses include doctor visits, prescriptions, and medical care",
                                "document": "HSA_Qualified_Expenses.txt"
                            }
                        elif "account" in chunk_id or "mgmt" in chunk_id:
                            metadata[chunk_id] = {
                                "text": "HSA accounts can be opened through banks and offer investment options",
                                "document": "HSA_Account_Management.txt"
                            }
                    
                    rag_service.vector_store.metadata = metadata
                    
                    response = await rag_service.answer_question(request)
                    
                    # Evaluate response accuracy
                    answer_lower = response.answer.lower()
                    keyword_matches = sum(1 for keyword in qa_pair["expected_keywords"] if keyword.lower() in answer_lower)
                    accuracy = keyword_matches / len(qa_pair["expected_keywords"])
                    accuracy_scores.append(accuracy)
                    
                    # Verify confidence levels
                    if "min_confidence" in qa_pair:
                        assert response.confidence_score >= qa_pair["min_confidence"], f"Low confidence for: {qa_pair['question']}"
                    if "max_confidence" in qa_pair:
                        assert response.confidence_score <= qa_pair["max_confidence"], f"High confidence for non-HSA question: {qa_pair['question']}"
                    
                    # Verify citations for high-confidence answers
                    if response.confidence_score > 0.6:
                        assert len(response.citations) > 0, f"No citations for high-confidence answer: {qa_pair['question']}"
                        assert len(response.source_documents) > 0
            
            # Overall accuracy should be reasonable
            overall_accuracy = sum(accuracy_scores) / len(accuracy_scores)
            assert overall_accuracy > 0.6, f"Overall accuracy too low: {overall_accuracy}"

    @pytest.mark.asyncio
    async def test_rag_metrics_collection(self):
        """Test RAG metrics collection and reporting."""
        with patch('backend.services.rag_service.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_embeddings = AsyncMock()
            mock_embeddings.create.return_value.data = [
                MagicMock(embedding=np.random.rand(100).tolist())
            ]
            mock_client.embeddings = mock_embeddings
            
            # Mock fast chat responses
            mock_chat = AsyncMock()
            mock_chat.completions.create.return_value = MagicMock(
                choices=[MagicMock(message=MagicMock(content="Test response"))]
            )
            mock_client.chat = mock_chat
            mock_openai.return_value = mock_client
            
            rag_service = RAGService(str(self.knowledge_base_path))
            
            # Simulate processing multiple queries
            test_queries = [
                "What are HSA contribution limits?",
                "Who is eligible for an HSA?",
                "What are qualified expenses?",
                "How do I open an HSA account?",
                "What is the weather?",  # Should have low confidence
            ]
            
            for query in test_queries:
                with patch.object(rag_service.vector_store, 'similarity_search') as mock_search:
                    if "weather" in query.lower():
                        mock_search.return_value = []  # No results for non-HSA query
                    else:
                        mock_search.return_value = [("chunk1", 0.85), ("chunk2", 0.80)]
                        rag_service.vector_store.metadata = {
                            "chunk1": {"text": "HSA information", "document": "HSA_FAQ.txt"},
                            "chunk2": {"text": "More HSA info", "document": "HSA_Guide.txt"}
                        }
                    
                    request = QARequest(question=query)
                    await rag_service.answer_question(request)
            
            # Verify metrics collection
            assert rag_service.query_count == 5
            assert len(rag_service.confidence_scores) == 5
            assert rag_service.total_response_time > 0
            
            # Get RAG metrics
            metrics = await rag_service.get_rag_metrics()
            
            # Verify metrics structure and values
            assert metrics.total_queries == 5
            assert metrics.average_response_time_ms > 0
            assert 0.0 <= metrics.average_confidence_score <= 1.0
            assert 0.0 <= metrics.citation_rate <= 1.0
            assert 0.0 <= metrics.knowledge_coverage <= 1.0
            
            # Verify citation rate calculation
            high_confidence_queries = sum(1 for score in rag_service.confidence_scores if score > 0.5)
            expected_citation_rate = high_confidence_queries / len(rag_service.confidence_scores)
            assert abs(metrics.citation_rate - expected_citation_rate) < 0.1

    @pytest.mark.asyncio
    async def test_knowledge_base_coverage(self):
        """Test knowledge base coverage and completeness."""
        with patch('backend.services.rag_service.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_embeddings = AsyncMock()
            mock_embeddings.create.return_value.data = [
                MagicMock(embedding=np.random.rand(100).tolist())
            ]
            mock_client.embeddings = mock_embeddings
            mock_openai.return_value = mock_client
            
            rag_service = RAGService(str(self.knowledge_base_path))
            await rag_service.build_knowledge_base()
            
            # Test knowledge base statistics
            stats = await rag_service.get_knowledge_base_stats()
            
            # Verify comprehensive coverage
            assert stats.total_documents == 4  # All test documents loaded
            assert stats.total_chunks > 10  # Reasonable chunking
            assert stats.total_embeddings == stats.total_chunks  # All chunks embedded
            assert stats.average_chunk_size > 100  # Reasonable chunk sizes
            
            # Verify all expected documents are indexed
            expected_documents = [
                "HSA_Contribution_Limits.txt",
                "HSA_Eligibility_Requirements.txt", 
                "HSA_Qualified_Expenses.txt",
                "HSA_Account_Management.txt"
            ]
            
            for doc in expected_documents:
                assert doc in rag_service.knowledge_base_index
                doc_info = rag_service.knowledge_base_index[doc]
                assert doc_info.chunk_count > 0
                assert doc_info.content_length > 500  # Substantial content


class TestRAGAccuracy:
    """Accuracy-focused tests for RAG system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.knowledge_base_path = Path(self.temp_dir) / "knowledge_base"
        self.knowledge_base_path.mkdir()
        
        # Create focused test documents for accuracy testing
        (self.knowledge_base_path / "HSA_Facts.txt").write_text("""
HSA Contribution Limits for 2024:
- Self-only coverage: $4,150
- Family coverage: $8,300
- Catch-up contribution (age 55+): $1,000

HSA Eligibility Requirements:
1. Must have qualified High Deductible Health Plan (HDHP)
2. Cannot have other health coverage
3. Cannot be enrolled in Medicare
4. Cannot be claimed as dependent

HDHP Requirements 2024:
- Self-only minimum deductible: $1,600
- Family minimum deductible: $3,200
- Self-only maximum out-of-pocket: $8,050
- Family maximum out-of-pocket: $16,100
        """.strip())

    def teardown_method(self):
        """Clean up temporary files."""
        shutil.rmtree(self.temp_dir)

    @pytest.mark.asyncio
    async def test_citation_accuracy(self):
        """Test that citations accurately reflect source content."""
        with patch('backend.services.rag_service.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_embeddings = AsyncMock()
            mock_embeddings.create.return_value.data = [
                MagicMock(embedding=np.random.rand(100).tolist())
            ]
            mock_client.embeddings = mock_embeddings
            
            # Mock chat to include source references
            mock_chat = AsyncMock()
            mock_chat.completions.create.return_value = MagicMock(
                choices=[MagicMock(message=MagicMock(
                    content="According to HSA_Facts.txt, the HSA contribution limits for 2024 are $4,150 for self-only coverage and $8,300 for family coverage."
                ))]
            )
            mock_client.chat = mock_chat
            mock_openai.return_value = mock_client
            
            rag_service = RAGService(str(self.knowledge_base_path))
            await rag_service.build_knowledge_base()
            
            # Test citation accuracy
            with patch.object(rag_service.vector_store, 'similarity_search') as mock_search:
                mock_search.return_value = [("chunk1", 0.95)]
                rag_service.vector_store.metadata = {
                    "chunk1": {
                        "text": "HSA Contribution Limits for 2024: Self-only coverage: $4,150, Family coverage: $8,300",
                        "document": "HSA_Facts.txt"
                    }
                }
                
                request = QARequest(question="What are the HSA contribution limits?")
                response = await rag_service.answer_question(request)
                
                # Verify citation accuracy
                assert len(response.citations) > 0
                citation = response.citations[0]
                
                # Citation should reference correct document
                assert citation.document_name == "HSA_Facts.txt"
                
                # Citation excerpt should contain relevant information
                assert "4,150" in citation.excerpt or "contribution" in citation.excerpt.lower()
                
                # Relevance score should be high for good matches
                assert citation.relevance_score > 0.7

    @pytest.mark.asyncio 
    async def test_confidence_score_accuracy(self):
        """Test that confidence scores accurately reflect answer quality."""
        with patch('backend.services.rag_service.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_embeddings = AsyncMock()
            mock_embeddings.create.return_value.data = [
                MagicMock(embedding=np.random.rand(100).tolist())
            ]
            mock_client.embeddings = mock_embeddings
            
            # Mock different quality responses
            mock_chat = AsyncMock()
            def mock_chat_create(model, messages, **kwargs):
                user_content = messages[-1]['content'].lower()
                if 'contribution' in user_content:
                    return MagicMock(choices=[MagicMock(message=MagicMock(
                        content="The HSA contribution limits for 2024 are clearly defined as $4,150 for individual coverage and $8,300 for family coverage."
                    ))])
                else:
                    return MagicMock(choices=[MagicMock(message=MagicMock(
                        content="I'm not sure about that."
                    ))])
            
            mock_chat.completions.create.side_effect = mock_chat_create
            mock_client.chat = mock_chat
            mock_openai.return_value = mock_client
            
            rag_service = RAGService(str(self.knowledge_base_path))
            
            # Test high-confidence scenario
            with patch.object(rag_service.vector_store, 'similarity_search') as mock_search:
                # High similarity results
                mock_search.return_value = [("chunk1", 0.95), ("chunk2", 0.90), ("chunk3", 0.85)]
                rag_service.vector_store.metadata = {
                    "chunk1": {"text": "HSA contribution limits 2024 are $4,150 and $8,300", "document": "HSA_Facts.txt"},
                    "chunk2": {"text": "Self-only coverage limit is $4,150", "document": "HSA_Facts.txt"},
                    "chunk3": {"text": "Family coverage limit is $8,300", "document": "HSA_Facts.txt"}
                }
                
                request = QARequest(question="What are HSA contribution limits?")
                response = await rag_service.answer_question(request)
                
                # Should have high confidence
                assert response.confidence_score > 0.8
                
            # Test low-confidence scenario  
            with patch.object(rag_service.vector_store, 'similarity_search') as mock_search:
                # Low similarity results
                mock_search.return_value = [("chunk1", 0.4)]
                rag_service.vector_store.metadata = {
                    "chunk1": {"text": "Some unrelated HSA information", "document": "HSA_Facts.txt"}
                }
                
                request = QARequest(question="What is quantum physics?")
                response = await rag_service.answer_question(request)
                
                # Should have low confidence
                assert response.confidence_score < 0.5
                
            # Test no results scenario
            with patch.object(rag_service.vector_store, 'similarity_search') as mock_search:
                mock_search.return_value = []  # No similar results
                
                request = QARequest(question="Tell me about astronomy")
                response = await rag_service.answer_question(request)
                
                # Should have zero confidence
                assert response.confidence_score == 0.0
                assert len(response.citations) == 0

    @pytest.mark.asyncio
    async def test_fallback_response_quality(self):
        """Test quality of fallback responses for unknown questions."""
        with patch('backend.services.rag_service.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_embeddings = AsyncMock()
            mock_embeddings.create.return_value.data = [
                MagicMock(embedding=np.random.rand(100).tolist())
            ]
            mock_client.embeddings = mock_embeddings
            mock_openai.return_value = mock_client
            
            rag_service = RAGService(str(self.knowledge_base_path))
            
            # Test fallback for non-HSA questions
            with patch.object(rag_service.vector_store, 'similarity_search') as mock_search:
                mock_search.return_value = []  # No relevant results
                
                non_hsa_questions = [
                    "What is the capital of France?",
                    "How do I cook pasta?",
                    "What's the weather like?",
                    "Tell me about machine learning"
                ]
                
                for question in non_hsa_questions:
                    request = QARequest(question=question)
                    response = await rag_service.answer_question(request)
                    
                    # Verify fallback response quality
                    assert response.confidence_score == 0.0
                    assert len(response.citations) == 0
                    assert len(response.source_documents) == 0
                    
                    # Fallback message should be helpful
                    fallback_indicators = [
                        "don't have information",
                        "knowledge base",
                        "HSA eligibility",
                        "contribution limits",
                        "qualified expenses",
                        "rephrase"
                    ]
                    
                    assert any(indicator in response.answer.lower() for indicator in fallback_indicators)

    @pytest.mark.asyncio
    async def test_context_handling_accuracy(self):
        """Test that context is properly handled in responses."""
        with patch('backend.services.rag_service.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_embeddings = AsyncMock()
            mock_embeddings.create.return_value.data = [
                MagicMock(embedding=np.random.rand(100).tolist())
            ]
            mock_client.embeddings = mock_embeddings
            
            # Mock context-aware responses
            mock_chat = AsyncMock()
            def mock_chat_create(model, messages, **kwargs):
                user_content = messages[-1]['content']
                if 'individual coverage' in user_content.lower():
                    return MagicMock(choices=[MagicMock(message=MagicMock(
                        content="For individual coverage, the HSA contribution limit for 2024 is $4,150."
                    ))])
                elif 'family coverage' in user_content.lower():
                    return MagicMock(choices=[MagicMock(message=MagicMock(
                        content="For family coverage, the HSA contribution limit for 2024 is $8,300."
                    ))])
                else:
                    return MagicMock(choices=[MagicMock(message=MagicMock(
                        content="The HSA contribution limits are $4,150 for individual and $8,300 for family coverage."
                    ))])
            
            mock_chat.completions.create.side_effect = mock_chat_create
            mock_client.chat = mock_chat
            mock_openai.return_value = mock_client
            
            rag_service = RAGService(str(self.knowledge_base_path))
            
            with patch.object(rag_service.vector_store, 'similarity_search') as mock_search:
                mock_search.return_value = [("chunk1", 0.9)]
                rag_service.vector_store.metadata = {
                    "chunk1": {"text": "HSA limits: individual $4,150, family $8,300", "document": "HSA_Facts.txt"}
                }
                
                # Test context-aware responses
                test_cases = [
                    {
                        "question": "What is the contribution limit?",
                        "context": "I have individual coverage",
                        "expected_content": "4,150"
                    },
                    {
                        "question": "What is the contribution limit?", 
                        "context": "I have family coverage",
                        "expected_content": "8,300"
                    }
                ]
                
                for test_case in test_cases:
                    request = QARequest(
                        question=test_case["question"],
                        context=test_case["context"]
                    )
                    response = await rag_service.answer_question(request)
                    
                    # Verify context was considered
                    assert test_case["expected_content"] in response.answer
                    assert response.confidence_score > 0.7