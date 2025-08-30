# OpenAI Vector Store Setup Guide

This guide explains how to set up and use the new OpenAI Vector Store integration for the HSA Assistant.

## Overview

The HSA Assistant has been reimplemented using the OpenAI Vector Stores API following the patterns from the OpenAI cookbook. This provides:

- **Production-ready RAG**: Uses OpenAI's native file_search capability
- **Proper citations**: Automatic citation extraction from OpenAI annotations
- **Scalable architecture**: No custom vector storage or embeddings management
- **Simple maintenance**: Just upload the IRS PDF to OpenAI's vector store

## Required Environment Variables

```bash
# Required: Your OpenAI API key
OPENAI_API_KEY=sk-...

# Optional: Vector Store ID (will be created if not provided)
OPENAI_VECTOR_STORE_ID=vs_...
```

## Setup Process

### 1. Install Dependencies

Ensure you have the latest OpenAI Python library:

```bash
pip install openai>=1.0.0
```

### 2. Set Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
# OPENAI_VECTOR_STORE_ID will be set automatically after first run
```

### 3. Ensure IRS PDF is Available

The system expects the IRS PDF at:
```
data/knowledge_base/hsa/irs.pdf
```

This file should be the official IRS Publication 969.

### 4. Initialize the Vector Store

Run the test script to initialize:

```bash
python test_openai_vector_store.py
```

Or use the API endpoint:

```bash
curl -X POST http://localhost:8000/api/v1/hsa_assistant/rebuild
```

## API Changes

### New Service Architecture

- **Before**: Custom RAG with local embeddings (`rag_service.py`)
- **After**: OpenAI Vector Store integration (`openai_vector_store_service.py`)

### API Endpoints (No Changes)

All existing endpoints work the same:

- `POST /hsa_assistant/ask` - Ask questions about HSA rules
- `POST /hsa_assistant/search` - Vector similarity search  
- `GET /hsa_assistant/stats` - Knowledge base statistics
- `GET /hsa_assistant/metrics` - Performance metrics
- `POST /hsa_assistant/rebuild` - Rebuild vector store
- `GET /hsa_assistant/health` - Health check

### Enhanced Features

1. **Better Citations**: OpenAI automatically provides proper citations with page numbers and file references
2. **Improved Accuracy**: Uses OpenAI's advanced embedding and retrieval models
3. **Auto-scaling**: No need to manage vector storage or compute resources
4. **Faster Responses**: Optimized retrieval through OpenAI's infrastructure

## Implementation Details

### Key Components

1. **Vector Store Creation**: 
   ```python
   vector_store = client.beta.vector_stores.create(name="hsa_knowledge_base")
   ```

2. **File Upload (Two-step)**:
   ```python
   # Step 1: Upload file
   file = client.files.create(file=open("irs.pdf", "rb"), purpose="assistants")
   
   # Step 2: Attach to vector store
   client.beta.vector_stores.files.create(
       vector_store_id=vector_store.id, 
       file_id=file.id
   )
   ```

3. **Assistant with File Search**:
   ```python
   assistant = client.beta.assistants.create(
       name="HSA Assistant",
       model="gpt-4o-mini",
       tools=[{"type": "file_search"}],
       tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}}
   )
   ```

4. **RAG Query Processing**:
   - Creates thread with user question
   - Runs assistant with file_search enabled
   - Extracts response and citations
   - Returns structured QAResponse

### Error Handling

The service includes comprehensive error handling for:
- OpenAI API failures
- File upload issues
- Vector store creation problems
- Assistant run failures
- Network timeouts

### Performance Monitoring

Built-in metrics tracking:
- Query count and response times
- Confidence scores and citation rates
- Knowledge coverage statistics
- System health indicators

## Testing

Run the comprehensive test suite:

```bash
python test_openai_vector_store.py
```

This will test:
- Environment configuration
- Vector store creation
- File upload process  
- Q&A functionality
- Vector search capabilities
- Performance metrics
- Health checks

## Migration from Custom RAG

The migration is backwards-compatible:
- Same API endpoints and request/response formats
- Same database schema for history tracking
- Same error handling patterns
- Enhanced citation quality and accuracy

## Troubleshooting

### Common Issues

1. **"Vector store not initialized"**
   - Run the `/rebuild` endpoint
   - Check that IRS PDF exists at correct path
   - Verify OPENAI_API_KEY is valid

2. **"File processing timeout"**
   - PDF processing can take 5-10 minutes
   - Check OpenAI dashboard for processing status
   - Retry if needed

3. **"Assistant creation failed"**
   - Verify OpenAI API key has assistant access
   - Check API quotas and limits
   - Ensure vector store exists

4. **Poor response quality**
   - Check that correct IRS PDF was uploaded
   - Verify vector store has processed files
   - Review assistant instructions

### Debug Information

Check service health:
```bash
curl http://localhost:8000/api/v1/hsa_assistant/health
```

Key health indicators:
- `vector_store_initialized`: Vector store ID is set
- `vector_store_healthy`: Vector store is accessible and completed
- `assistant_id`: Assistant is created and ready
- `knowledge_base_path_exists`: Source PDF is available

## Production Considerations

1. **API Costs**: Monitor OpenAI usage for file storage and query costs
2. **Rate Limits**: Implement appropriate request throttling
3. **Monitoring**: Set up alerts for service health and response quality  
4. **Backup**: Keep OPENAI_VECTOR_STORE_ID for disaster recovery
5. **Updates**: Process for updating knowledge base with new IRS publications

## Support

For issues specific to this implementation:
1. Check the test output for detailed error messages
2. Review OpenAI dashboard for vector store status
3. Verify all environment variables are correctly set
4. Check server logs for detailed error traces