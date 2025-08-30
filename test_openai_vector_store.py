"""
Test script for OpenAI Vector Store Service implementation.

This script tests the key functionality of the HSA Assistant using
the new OpenAI Vector Stores API integration.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend directory to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from services.openai_vector_store_service import OpenAIVectorStoreService, OpenAIVectorStoreError
from schemas.hsa_assistant import QARequest, VectorSearchRequest


async def test_vector_store_service():
    """Test the OpenAI Vector Store Service functionality."""
    
    print("🚀 Testing OpenAI Vector Store Service")
    print("=" * 50)
    
    # Initialize service
    service = OpenAIVectorStoreService()
    
    # Test 1: Health Check (before initialization)
    print("\n📊 Test 1: Health Check (before initialization)")
    try:
        health = await service.health_check()
        print(f"Health Status: {health['status']}")
        print(f"Vector Store Initialized: {health['vector_store_initialized']}")
        print(f"OpenAI Client Configured: {health['openai_client_configured']}")
        print(f"Knowledge Base Path Exists: {health['knowledge_base_path_exists']}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    # Test 2: Upload Knowledge Base (IRS PDF)
    print("\n📚 Test 2: Upload Knowledge Base")
    try:
        await service.upload_knowledge_base()
        print("✅ Knowledge base uploaded successfully")
        print(f"Vector Store ID: {service.vector_store_id}")
    except OpenAIVectorStoreError as e:
        print(f"❌ Knowledge base upload failed: {e}")
        print("🔧 This is expected if OPENAI_VECTOR_STORE_ID is not set or IRS PDF is not available")
        
        # Try to create a new vector store
        try:
            print("🔧 Attempting to create new vector store...")
            vector_store_id = await service.create_vector_store()
            print(f"✅ New vector store created: {vector_store_id}")
            print("⚠️ Remember to set OPENAI_VECTOR_STORE_ID environment variable to:", vector_store_id)
        except Exception as create_error:
            print(f"❌ Failed to create vector store: {create_error}")
            return
    
    # Test 3: Health Check (after initialization)
    print("\n📊 Test 3: Health Check (after initialization)")
    try:
        health = await service.health_check()
        print(f"Health Status: {health['status']}")
        print(f"Vector Store Healthy: {health.get('vector_store_healthy', 'N/A')}")
        print(f"Assistant ID: {health.get('assistant_id', 'Not created yet')}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    # Test 4: Knowledge Base Stats
    print("\n📈 Test 4: Knowledge Base Statistics")
    try:
        stats = await service.get_knowledge_base_stats()
        print(f"Total Documents: {stats.total_documents}")
        print(f"Total Chunks: {stats.total_chunks}")
        print(f"Total Embeddings: {stats.total_embeddings}")
        print(f"Average Chunk Size: {stats.average_chunk_size}")
    except Exception as e:
        print(f"❌ Stats retrieval failed: {e}")
    
    # Test 5: Vector Search
    print("\n🔍 Test 5: Vector Search")
    try:
        search_request = VectorSearchRequest(
            query="HSA contribution limits 2024",
            k=3
        )
        results = await service.vector_search(search_request)
        print(f"Found {len(results)} search results")
        for i, result in enumerate(results):
            print(f"  {i+1}. Document: {result.document_name}")
            print(f"     Similarity: {result.similarity_score:.2f}")
            print(f"     Text: {result.text[:100]}...")
    except Exception as e:
        print(f"❌ Vector search failed: {e}")
    
    # Test 6: Q&A (Main functionality)
    print("\n💬 Test 6: Question Answering")
    try:
        qa_request = QARequest(
            question="What are the HSA contribution limits for 2024?",
            application_id="test-app-123"
        )
        response = await service.answer_question(qa_request)
        print(f"✅ Question answered successfully")
        print(f"Confidence Score: {response.confidence_score:.2f}")
        print(f"Citations: {len(response.citations)}")
        print(f"Source Documents: {response.source_documents}")
        print(f"Processing Time: {response.processing_time_ms}ms")
        print(f"Answer: {response.answer[:300]}...")
        
        if response.citations:
            print("\n📚 Citations:")
            for i, citation in enumerate(response.citations):
                print(f"  {i+1}. {citation.document_name} (Score: {citation.relevance_score:.2f})")
                print(f"     {citation.excerpt[:150]}...")
    except Exception as e:
        print(f"❌ Question answering failed: {e}")
    
    # Test 7: RAG Metrics
    print("\n📊 Test 7: RAG Performance Metrics")
    try:
        metrics = await service.get_rag_metrics()
        print(f"Total Queries: {metrics.total_queries}")
        print(f"Average Response Time: {metrics.average_response_time_ms:.1f}ms")
        print(f"Average Confidence: {metrics.average_confidence_score:.2f}")
        print(f"Citation Rate: {metrics.citation_rate:.1%}")
        print(f"Knowledge Coverage: {metrics.knowledge_coverage:.1%}")
    except Exception as e:
        print(f"❌ Metrics retrieval failed: {e}")
    
    print("\n✅ OpenAI Vector Store Service testing completed!")


def check_environment():
    """Check if required environment variables are set."""
    print("🔧 Environment Check")
    print("=" * 30)
    
    openai_key = os.getenv("OPENAI_API_KEY")
    vector_store_id = os.getenv("OPENAI_VECTOR_STORE_ID")
    
    if openai_key:
        print("✅ OPENAI_API_KEY is set")
    else:
        print("❌ OPENAI_API_KEY is not set")
        return False
    
    if vector_store_id:
        print(f"✅ OPENAI_VECTOR_STORE_ID is set: {vector_store_id}")
    else:
        print("⚠️ OPENAI_VECTOR_STORE_ID is not set (will create new vector store)")
    
    # Check if IRS PDF exists
    irs_pdf_path = Path("data/knowledge_base/hsa/irs.pdf")
    if irs_pdf_path.exists():
        print(f"✅ IRS PDF found: {irs_pdf_path}")
        print(f"   File size: {irs_pdf_path.stat().st_size / 1024 / 1024:.1f} MB")
    else:
        print(f"❌ IRS PDF not found: {irs_pdf_path}")
        print("   This will cause upload to fail")
    
    return True


if __name__ == "__main__":
    print("🧪 HSA Assistant - OpenAI Vector Store Test")
    print("=" * 60)
    
    if not check_environment():
        print("\n❌ Environment check failed. Please set required environment variables.")
        sys.exit(1)
    
    try:
        asyncio.run(test_vector_store_service())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()