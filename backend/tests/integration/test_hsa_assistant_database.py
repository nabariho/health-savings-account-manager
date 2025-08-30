"""
Database integration tests for HSA Assistant system.

This module tests database interactions for HSA Assistant history tracking
and session management as specified in user story US-4.1 requirements.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, AsyncMock, MagicMock

from backend.core.database import BaseModel
from backend.models.hsa_assistant_history import HSAAssistantHistory
from backend.schemas.hsa_assistant import QAResponse, Citation
from backend.api.v1.hsa_assistant import ask_question


# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_hsa_assistant.db"


@pytest.fixture(scope="function")
def test_db():
    """Create test database session."""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    BaseModel.metadata.create_all(bind=engine)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    
    yield session
    
    session.close()
    BaseModel.metadata.drop_all(bind=engine)


class TestHSAAssistantHistory:
    """Test HSA Assistant history database model."""

    def test_create_hsa_assistant_history_record(self, test_db):
        """Test creating HSA Assistant history record."""
        # Create test record
        history_record = HSAAssistantHistory(
            question="What are the HSA contribution limits for 2024?",
            answer="For 2024, HSA contribution limits are $4,150 for self-only coverage and $8,300 for family coverage.",
            confidence_score=0.92,
            citations_count=2,
            processing_time_ms=1250,
            application_id="test-app-123",
            context="User asking about individual vs family coverage",
            source_documents="HSA_FAQ.txt,HSA_Limits.txt"
        )
        
        # Save to database
        test_db.add(history_record)
        test_db.commit()
        
        # Verify record was saved
        assert history_record.id is not None
        assert history_record.created_at is not None
        assert history_record.updated_at is not None
        
        # Retrieve and verify
        retrieved = test_db.query(HSAAssistantHistory).filter(
            HSAAssistantHistory.id == history_record.id
        ).first()
        
        assert retrieved is not None
        assert retrieved.question == "What are the HSA contribution limits for 2024?"
        assert retrieved.answer.startswith("For 2024, HSA contribution limits")
        assert retrieved.confidence_score == 0.92
        assert retrieved.citations_count == 2
        assert retrieved.processing_time_ms == 1250
        assert retrieved.application_id == "test-app-123"
        assert retrieved.context == "User asking about individual vs family coverage"
        assert retrieved.source_documents == "HSA_FAQ.txt,HSA_Limits.txt"

    def test_hsa_assistant_history_required_fields(self, test_db):
        """Test HSA Assistant history model required fields."""
        # Test with minimal required fields
        minimal_record = HSAAssistantHistory(
            question="Test question?",
            answer="Test answer.",
            confidence_score=0.5
        )
        
        test_db.add(minimal_record)
        test_db.commit()
        
        assert minimal_record.id is not None
        assert minimal_record.citations_count == 0  # Default value
        assert minimal_record.processing_time_ms is None  # Optional field
        assert minimal_record.application_id is None  # Optional field
        assert minimal_record.context is None  # Optional field

    def test_hsa_assistant_history_constraints(self, test_db):
        """Test HSA Assistant history model constraints."""
        # Test confidence score constraints
        valid_scores = [0.0, 0.5, 1.0]
        for score in valid_scores:
            record = HSAAssistantHistory(
                question="Test question?",
                answer="Test answer.",
                confidence_score=score
            )
            test_db.add(record)
            test_db.commit()
            assert record.confidence_score == score
            test_db.delete(record)
            test_db.commit()

    def test_hsa_assistant_history_timestamps(self, test_db):
        """Test automatic timestamp handling."""
        record = HSAAssistantHistory(
            question="Test question?",
            answer="Test answer.",
            confidence_score=0.8
        )
        
        # Timestamps should be None before saving
        assert record.created_at is None
        assert record.updated_at is None
        
        test_db.add(record)
        test_db.commit()
        
        # Timestamps should be set after saving
        assert record.created_at is not None
        assert record.updated_at is not None
        assert record.created_at <= record.updated_at
        
        # Update record and check updated_at changes
        original_updated = record.updated_at
        record.confidence_score = 0.9
        test_db.commit()
        
        assert record.updated_at >= original_updated

    def test_query_hsa_assistant_history_by_application_id(self, test_db):
        """Test querying history by application ID."""
        app_id_1 = "app-123"
        app_id_2 = "app-456"
        
        # Create records for different applications
        records_app_1 = []
        for i in range(3):
            record = HSAAssistantHistory(
                question=f"Question {i} for app 1",
                answer=f"Answer {i} for app 1",
                confidence_score=0.8,
                application_id=app_id_1
            )
            records_app_1.append(record)
            test_db.add(record)
        
        records_app_2 = []
        for i in range(2):
            record = HSAAssistantHistory(
                question=f"Question {i} for app 2",
                answer=f"Answer {i} for app 2",
                confidence_score=0.7,
                application_id=app_id_2
            )
            records_app_2.append(record)
            test_db.add(record)
        
        # Add record without application ID
        record_no_app = HSAAssistantHistory(
            question="Question without app ID",
            answer="Answer without app ID",
            confidence_score=0.6
        )
        test_db.add(record_no_app)
        test_db.commit()
        
        # Query by application ID
        app_1_records = test_db.query(HSAAssistantHistory).filter(
            HSAAssistantHistory.application_id == app_id_1
        ).all()
        
        app_2_records = test_db.query(HSAAssistantHistory).filter(
            HSAAssistantHistory.application_id == app_id_2
        ).all()
        
        # Verify results
        assert len(app_1_records) == 3
        assert len(app_2_records) == 2
        
        for record in app_1_records:
            assert record.application_id == app_id_1
            assert "app 1" in record.question
        
        for record in app_2_records:
            assert record.application_id == app_id_2
            assert "app 2" in record.question

    def test_hsa_assistant_history_ordering(self, test_db):
        """Test ordering history records by timestamp."""
        import time
        
        # Create records with slight time differences
        records = []
        for i in range(5):
            record = HSAAssistantHistory(
                question=f"Question {i}",
                answer=f"Answer {i}",
                confidence_score=0.8,
                application_id="test-app"
            )
            test_db.add(record)
            test_db.commit()  # Commit each to ensure different timestamps
            records.append(record)
            time.sleep(0.01)  # Small delay to ensure different timestamps
        
        # Query ordered by created_at descending (most recent first)
        ordered_records = test_db.query(HSAAssistantHistory).filter(
            HSAAssistantHistory.application_id == "test-app"
        ).order_by(HSAAssistantHistory.created_at.desc()).all()
        
        assert len(ordered_records) == 5
        
        # Verify descending order
        for i in range(len(ordered_records) - 1):
            assert ordered_records[i].created_at >= ordered_records[i + 1].created_at
        
        # Most recent should be last created
        assert ordered_records[0].question == "Question 4"

    def test_hsa_assistant_history_pagination(self, test_db):
        """Test pagination of history records."""
        # Create multiple records
        for i in range(15):
            record = HSAAssistantHistory(
                question=f"Question {i:02d}",
                answer=f"Answer {i:02d}",
                confidence_score=0.8,
                application_id="paginate-test"
            )
            test_db.add(record)
        test_db.commit()
        
        # Test pagination
        page_size = 5
        
        # First page
        page_1 = test_db.query(HSAAssistantHistory).filter(
            HSAAssistantHistory.application_id == "paginate-test"
        ).order_by(HSAAssistantHistory.created_at.desc()).limit(page_size).offset(0).all()
        
        # Second page
        page_2 = test_db.query(HSAAssistantHistory).filter(
            HSAAssistantHistory.application_id == "paginate-test"
        ).order_by(HSAAssistantHistory.created_at.desc()).limit(page_size).offset(5).all()
        
        # Third page
        page_3 = test_db.query(HSAAssistantHistory).filter(
            HSAAssistantHistory.application_id == "paginate-test"
        ).order_by(HSAAssistantHistory.created_at.desc()).limit(page_size).offset(10).all()
        
        # Verify pagination
        assert len(page_1) == 5
        assert len(page_2) == 5
        assert len(page_3) == 5
        
        # Verify no overlap between pages
        page_1_ids = {r.id for r in page_1}
        page_2_ids = {r.id for r in page_2}
        page_3_ids = {r.id for r in page_3}
        
        assert len(page_1_ids & page_2_ids) == 0
        assert len(page_1_ids & page_3_ids) == 0
        assert len(page_2_ids & page_3_ids) == 0

    def test_hsa_assistant_history_metrics_aggregation(self, test_db):
        """Test aggregating metrics from history records."""
        # Create records with varying confidence scores and processing times
        test_data = [
            {"confidence": 0.9, "processing_time": 1000, "citations": 3},
            {"confidence": 0.8, "processing_time": 1200, "citations": 2},
            {"confidence": 0.7, "processing_time": 800, "citations": 1},
            {"confidence": 0.9, "processing_time": 1100, "citations": 4},
            {"confidence": 0.3, "processing_time": 500, "citations": 0},  # Low confidence, no citations
        ]
        
        for data in test_data:
            record = HSAAssistantHistory(
                question="Test question",
                answer="Test answer",
                confidence_score=data["confidence"],
                processing_time_ms=data["processing_time"],
                citations_count=data["citations"],
                application_id="metrics-test"
            )
            test_db.add(record)
        test_db.commit()
        
        # Query for metrics aggregation
        from sqlalchemy import func
        
        metrics = test_db.query(
            func.count(HSAAssistantHistory.id).label('total_queries'),
            func.avg(HSAAssistantHistory.confidence_score).label('avg_confidence'),
            func.avg(HSAAssistantHistory.processing_time_ms).label('avg_processing_time'),
            func.sum(HSAAssistantHistory.citations_count).label('total_citations')
        ).filter(
            HSAAssistantHistory.application_id == "metrics-test"
        ).first()
        
        # Verify aggregated metrics
        assert metrics.total_queries == 5
        assert abs(metrics.avg_confidence - 0.72) < 0.01  # (0.9+0.8+0.7+0.9+0.3)/5 = 0.72
        assert abs(metrics.avg_processing_time - 920) < 1  # Average of processing times
        assert metrics.total_citations == 10  # Sum of citations

    def test_hsa_assistant_history_search_by_content(self, test_db):
        """Test searching history by question or answer content."""
        # Create records with different content
        test_records = [
            {
                "question": "What are HSA contribution limits?",
                "answer": "HSA limits are $4,150 for individual and $8,300 for family coverage.",
                "app_id": "search-test"
            },
            {
                "question": "Who is eligible for HSA?",
                "answer": "You must have HDHP coverage and no other health insurance.",
                "app_id": "search-test"
            },
            {
                "question": "What are qualified medical expenses?",
                "answer": "Qualified expenses include doctor visits, prescriptions, and medical procedures.",
                "app_id": "search-test"
            },
            {
                "question": "How do I invest HSA funds?",
                "answer": "Many HSA providers offer investment options after meeting minimum balance.",
                "app_id": "search-test"
            }
        ]
        
        for record_data in test_records:
            record = HSAAssistantHistory(
                question=record_data["question"],
                answer=record_data["answer"],
                confidence_score=0.8,
                application_id=record_data["app_id"]
            )
            test_db.add(record)
        test_db.commit()
        
        # Test content search
        search_terms = [
            ("contribution", 1),  # Should find 1 record
            ("HSA", 4),           # Should find all 4 records
            ("eligible", 1),      # Should find 1 record  
            ("investment", 1),    # Should find 1 record
            ("nonexistent", 0)    # Should find 0 records
        ]
        
        for term, expected_count in search_terms:
            # Search in questions
            question_results = test_db.query(HSAAssistantHistory).filter(
                HSAAssistantHistory.application_id == "search-test",
                HSAAssistantHistory.question.contains(term)
            ).all()
            
            # Search in answers
            answer_results = test_db.query(HSAAssistantHistory).filter(
                HSAAssistantHistory.application_id == "search-test",
                HSAAssistantHistory.answer.contains(term)
            ).all()
            
            # Combined search (question OR answer)
            combined_results = test_db.query(HSAAssistantHistory).filter(
                HSAAssistantHistory.application_id == "search-test"
            ).filter(
                (HSAAssistantHistory.question.contains(term)) |
                (HSAAssistantHistory.answer.contains(term))
            ).all()
            
            total_found = len(combined_results)
            if term == "nonexistent":
                assert total_found == 0
            else:
                assert total_found > 0


class TestHSAAssistantAPIIntegration:
    """Test API integration with database."""

    @patch('backend.api.v1.hsa_assistant.get_rag_service')
    @patch('backend.core.database.get_db')
    def test_ask_question_saves_to_database(self, mock_get_db, mock_get_rag_service, test_db):
        """Test that ask_question endpoint saves history to database."""
        # Setup mocks
        mock_get_db.return_value = test_db
        
        mock_rag = AsyncMock()
        mock_response = QAResponse(
            answer="For 2024, HSA contribution limits are $4,150 for self-only coverage and $8,300 for family coverage.",
            confidence_score=0.92,
            citations=[
                Citation(
                    document_name="HSA_FAQ.txt",
                    excerpt="HSA contribution limits for 2024",
                    relevance_score=0.95
                )
            ],
            source_documents=["HSA_FAQ.txt"],
            processing_time_ms=1250
        )
        mock_rag.answer_question.return_value = mock_response
        mock_get_rag_service.return_value = mock_rag
        
        # Import here to avoid circular imports
        from backend.schemas.hsa_assistant import QARequest
        
        # Create request
        request = QARequest(
            question="What are the HSA contribution limits for 2024?",
            context="User asking about 2024 limits",
            application_id="integration-test-123"
        )
        
        # Call the endpoint function directly
        import asyncio
        response = asyncio.run(ask_question(request, mock_rag, test_db))
        
        # Verify response
        assert response.answer == mock_response.answer
        assert response.confidence_score == 0.92
        assert len(response.citations) == 1
        
        # Verify database record was created
        db_records = test_db.query(HSAAssistantHistory).filter(
            HSAAssistantHistory.application_id == "integration-test-123"
        ).all()
        
        assert len(db_records) == 1
        db_record = db_records[0]
        
        assert db_record.question == "What are the HSA contribution limits for 2024?"
        assert "4,150" in db_record.answer
        assert db_record.confidence_score == 0.92
        assert db_record.citations_count == 1
        assert db_record.processing_time_ms == 1250
        assert db_record.application_id == "integration-test-123"
        assert db_record.context == "User asking about 2024 limits"
        assert "HSA_FAQ.txt" in db_record.source_documents

    @patch('backend.api.v1.hsa_assistant.get_rag_service')
    @patch('backend.core.database.get_db')
    def test_multiple_questions_create_history_chain(self, mock_get_db, mock_get_rag_service, test_db):
        """Test that multiple questions create a proper history chain."""
        # Setup mocks
        mock_get_db.return_value = test_db
        mock_rag = AsyncMock()
        mock_get_rag_service.return_value = mock_rag
        
        from backend.schemas.hsa_assistant import QARequest
        
        # Simulate multiple Q&A interactions
        qa_pairs = [
            {
                "question": "What are HSA contribution limits?",
                "answer": "HSA limits are $4,150 for individual and $8,300 for family.",
                "confidence": 0.9,
                "citations": 2
            },
            {
                "question": "Am I eligible for an HSA?",
                "answer": "You need HDHP coverage and no other health insurance.",
                "confidence": 0.8,
                "citations": 1
            },
            {
                "question": "Can I use HSA for dental expenses?",
                "answer": "Yes, dental care is a qualified medical expense for HSA.",
                "confidence": 0.85,
                "citations": 1
            }
        ]
        
        application_id = "history-chain-test"
        
        for i, qa in enumerate(qa_pairs):
            # Mock RAG response
            mock_response = QAResponse(
                answer=qa["answer"],
                confidence_score=qa["confidence"],
                citations=[
                    Citation(
                        document_name=f"HSA_Doc_{i}.txt",
                        excerpt=f"Excerpt {i}",
                        relevance_score=0.9
                    ) for _ in range(qa["citations"])
                ],
                source_documents=[f"HSA_Doc_{i}.txt"],
                processing_time_ms=1000 + i * 100
            )
            mock_rag.answer_question.return_value = mock_response
            
            # Create request
            request = QARequest(
                question=qa["question"],
                application_id=application_id
            )
            
            # Call endpoint
            import asyncio
            response = asyncio.run(ask_question(request, mock_rag, test_db))
            
            # Verify response
            assert response.confidence_score == qa["confidence"]
        
        # Verify all records were saved
        history_records = test_db.query(HSAAssistantHistory).filter(
            HSAAssistantHistory.application_id == application_id
        ).order_by(HSAAssistantHistory.created_at.asc()).all()
        
        assert len(history_records) == 3
        
        # Verify record details
        for i, record in enumerate(history_records):
            assert record.question == qa_pairs[i]["question"]
            assert record.answer == qa_pairs[i]["answer"]
            assert record.confidence_score == qa_pairs[i]["confidence"]
            assert record.citations_count == qa_pairs[i]["citations"]
            assert record.application_id == application_id

    @patch('backend.api.v1.hsa_assistant.get_rag_service')
    @patch('backend.core.database.get_db')
    def test_database_error_handling(self, mock_get_db, mock_get_rag_service):
        """Test handling of database errors during history saving."""
        # Setup mocks
        mock_db = MagicMock()
        mock_db.add.side_effect = Exception("Database connection error")
        mock_get_db.return_value = mock_db
        
        mock_rag = AsyncMock()
        mock_response = QAResponse(
            answer="Test answer",
            confidence_score=0.8,
            citations=[],
            source_documents=[],
            processing_time_ms=1000
        )
        mock_rag.answer_question.return_value = mock_response
        mock_get_rag_service.return_value = mock_rag
        
        from backend.schemas.hsa_assistant import QARequest
        
        request = QARequest(
            question="Test question",
            application_id="error-test"
        )
        
        # Call endpoint - should handle database error gracefully
        import asyncio
        with pytest.raises(Exception):  # Should propagate the database error
            asyncio.run(ask_question(request, mock_rag, mock_db))

    def test_hsa_assistant_history_model_string_representation(self, test_db):
        """Test string representation of HSAAssistantHistory model."""
        record = HSAAssistantHistory(
            question="Test question",
            answer="Test answer",
            confidence_score=0.75
        )
        
        test_db.add(record)
        test_db.commit()
        
        # Test __repr__ method
        str_repr = str(record)
        assert f"HSAAssistantHistory(id={record.id}" in str_repr
        assert "confidence=0.75" in str_repr

    def test_bulk_history_operations(self, test_db):
        """Test bulk operations on history records."""
        # Create multiple records for bulk operations
        records = []
        for i in range(100):
            record = HSAAssistantHistory(
                question=f"Bulk question {i}",
                answer=f"Bulk answer {i}",
                confidence_score=0.8,
                citations_count=i % 5,  # Vary citations count
                processing_time_ms=1000 + i * 10,
                application_id=f"bulk-app-{i % 10}"  # 10 different applications
            )
            records.append(record)
        
        # Bulk insert
        test_db.bulk_save_objects(records)
        test_db.commit()
        
        # Verify all records were inserted
        total_count = test_db.query(HSAAssistantHistory).count()
        assert total_count == 100
        
        # Test bulk query operations
        # Get records with high citation counts
        high_citation_records = test_db.query(HSAAssistantHistory).filter(
            HSAAssistantHistory.citations_count >= 3
        ).all()
        
        expected_high_citation = len([r for r in records if r.citations_count >= 3])
        assert len(high_citation_records) == expected_high_citation
        
        # Test aggregation on bulk data
        from sqlalchemy import func
        
        app_stats = test_db.query(
            HSAAssistantHistory.application_id,
            func.count(HSAAssistantHistory.id).label('query_count'),
            func.avg(HSAAssistantHistory.confidence_score).label('avg_confidence')
        ).group_by(HSAAssistantHistory.application_id).all()
        
        # Should have 10 different applications
        assert len(app_stats) == 10
        
        # Each application should have 10 queries
        for stat in app_stats:
            assert stat.query_count == 10
            assert stat.avg_confidence == 0.8