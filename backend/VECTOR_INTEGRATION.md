# FAISS Vector Database Integration

This document describes the FAISS vector database integration implemented in Phase 2.3 of the Business Capability Management System.

## 🎯 Overview

The vector database integration adds semantic search capabilities to the business capability management system using FAISS (Facebook AI Similarity Search) with Google Gemini embeddings. This allows for intelligent similarity matching across capabilities, business goals, and recommendations.

## 🏗️ Architecture

### Components

1. **VectorEmbedding Model** (`core/models.py`)
   - Stores metadata for vector embeddings
   - Links to original objects (Capability, BusinessGoal, CapabilityRecommendation)
   - Tracks embedding model and vector index positions

2. **VectorManager Service** (`core/vector_manager.py`)
   - Handles all FAISS operations
   - Manages separate indexes for different content types
   - Provides embedding generation using Gemini API

3. **Django Signals** (`core/signals.py`)
   - Automatic embedding generation on model save
   - Embedding cleanup on model delete
   - Ensures vector indexes stay synchronized

4. **Vector API Views** (`core/views.py`)
   - Vector search endpoints
   - Index management operations
   - Enhanced LLM queries with vector context

## 📊 Database Schema

### VectorEmbedding Model

```python
class VectorEmbedding(models.Model):
    id = UUIDField(primary_key=True)
    content_type = CharField(choices=['CAPABILITY', 'BUSINESS_GOAL', 'RECOMMENDATION'])
    object_id = UUIDField()  # Links to original object
    embedding_model = CharField(default='text-embedding-004')
    vector_index = IntegerField()  # Position in FAISS index
    text_content = TextField()  # Original text that was embedded
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

### FAISS Index Structure

- **capabilities.faiss** - Capability name + description embeddings
- **business_goals.faiss** - Goal title + description embeddings  
- **recommendations.faiss** - Recommendation details embeddings

## 🔍 API Endpoints

### Vector Management

- `GET /api/vectors/status/` - Get vector database health and statistics
- `POST /api/vectors/rebuild/` - Rebuild FAISS indexes from scratch
- `POST /api/vectors/optimize/` - Optimize indexes for performance

### Similarity Search

- `GET /api/capabilities/{id}/similar/?limit=5&threshold=0.7` - Find similar capabilities
- `GET /api/business-goals/{id}/similar/?limit=5&threshold=0.7` - Find similar goals
- `GET /api/recommendations/{id}/similar/?limit=5&threshold=0.7` - Find similar recommendations

### Enhanced AI Queries

- `POST /api/llm/query/` - LLM queries with automatic vector context retrieval

Note: The LLM query endpoint automatically includes vector context from similar capabilities, business goals, and recommendations to provide enhanced responses.

## 🚀 Usage Examples

### 1. Check Vector Database Status

```bash
curl -X GET "http://localhost:8000/api/vectors/status/"
```

### 2. Find Similar Capabilities

```bash
# Get capability ID first
CAPABILITY_ID=$(curl -s "http://localhost:8000/api/capabilities/" | jq -r '.results[0].id')

# Find similar capabilities
curl -X GET "http://localhost:8000/api/capabilities/$CAPABILITY_ID/similar/?limit=3&threshold=0.6"
```

### 3. Enhanced AI Query with Vector Context

```bash
curl -X POST "http://localhost:8000/api/llm/query/" \
  -H "Content-Type: application/json" \
  -d '{"query": "How can we improve customer retention?"}'
```

### 4. Rebuild Vector Indexes

```bash
curl -X POST "http://localhost:8000/api/vectors/rebuild/" \
  -H "Content-Type: application/json" \
  -d '{"operation": "rebuild", "indexes": ["capabilities", "business_goals"]}'
```

## ⚙️ Configuration

### Environment Variables

```bash
# Required for embeddings
GEMINI_API_KEY=your_gemini_api_key_here
```

### Django Settings

The vector storage directory is automatically created at:
```
backend/vector_storage/
├── capabilities.faiss
├── business_goals.faiss
├── recommendations.faiss
```

## 🔧 Implementation Details

### Embedding Generation

- **Model**: Google Gemini `text-embedding-004`
- **Dimension**: 768 vectors
- **Similarity**: Cosine similarity (using normalized vectors)
- **Index Type**: FAISS IndexFlatIP for exact search

### Automatic Embedding Updates

Django signals automatically handle:

1. **Object Creation**: Generate embedding when new objects are saved
2. **Object Updates**: Regenerate embedding when content changes
3. **Object Deletion**: Remove corresponding embedding
4. **Status Changes**: Remove embeddings for deprecated/archived capabilities

### Text Processing

Each content type uses specific text combinations for embeddings:

- **Capabilities**: `name + description`
- **Business Goals**: `title + description`
- **Recommendations**: `type + proposed_name + description + details + goal_title`

## 🧪 Testing

Run the comprehensive test suite:

```bash
cd backend
python test_vector_search.py
```

This tests:
- Vector database status
- Similarity search functionality
- Enhanced LLM queries
- Index rebuild operations
- Business goal analysis with vector context

## 📈 Performance Considerations

### Index Size

- ~1KB per embedding (768 float32 values)
- Indexes are stored on disk and loaded into memory
- Automatic index saving after updates

### Search Performance

- FAISS IndexFlatIP provides exact similarity search
- Search time scales linearly with index size
- For large datasets, consider IndexIVFFlat for approximate search

### Memory Usage

- Indexes are kept in memory for fast access
- Each index: ~768 bytes × number_of_vectors
- Monitor memory usage as data grows

## 🔄 Maintenance

### Regular Tasks

1. **Monitor Index Health**:
   ```bash
   curl -X GET "http://localhost:8000/api/vectors/status/"
   ```

2. **Rebuild Indexes** (if needed):
   ```bash
   curl -X POST "http://localhost:8000/api/vectors/rebuild/" \
     -H "Content-Type: application/json" \
     -d '{"operation": "rebuild", "indexes": ["capabilities"]}'
   ```

3. **Check Disk Usage**:
   ```bash
   ls -lh backend/vector_storage/
   ```

### Backup Strategy

- Vector indexes can be rebuilt from source data
- Backup the Django database (contains VectorEmbedding metadata)
- Consider backing up `vector_storage/` directory for faster recovery

## 🚧 Future Enhancements

### Potential Improvements

1. **GPU Support**: Switch to `faiss-gpu` for large datasets
2. **Approximate Search**: Use IndexIVFFlat for faster search on large indexes
3. **Batch Processing**: Batch embedding generation for better performance
4. **Caching**: Add Redis caching for frequent similarity searches
5. **Monitoring**: Add metrics and alerts for vector database health

### Scaling Considerations

- **Large Datasets**: Consider approximate search algorithms
- **High Traffic**: Implement search result caching
- **Distributed Setup**: Use separate vector service for multiple instances

## 📝 Troubleshooting

### Common Issues

1. **"No module named 'faiss'"**
   ```bash
   pip install faiss-cpu
   ```

2. **"GEMINI_API_KEY not set"**
   ```bash
   export GEMINI_API_KEY=your_key_here
   ```

3. **Empty search results**
   - Check similarity threshold (try lower values like 0.5)
   - Verify embeddings exist: `GET /api/vectors/status/`
   - Rebuild indexes if needed

4. **Out of memory errors**
   - Monitor index sizes: `GET /api/vectors/status/`
   - Consider using approximate search for large datasets

### Debug Commands

```bash
# Check Django admin for VectorEmbedding records
curl -X GET "http://localhost:8000/admin/"

# Verify FAISS files exist
ls -la backend/vector_storage/

# Test embedding generation manually
python manage.py shell
>>> from core.vector_manager import vector_manager
>>> vector_manager.generate_embedding("test text")
```

## 🎓 Learning Resources

- [FAISS Documentation](https://github.com/facebookresearch/faiss)
- [Google Generative AI Documentation](https://ai.google.dev/)
- [Vector Similarity Search Concepts](https://www.pinecone.io/learn/vector-similarity/)

---

## ✅ Ready for Frontend Integration

The vector database is now fully integrated and ready for frontend development. The next phase should implement:

1. **Semantic Search Components** - React components for vector-powered search
2. **Similarity Indicators** - UI elements showing relevance scores
3. **Smart Suggestions** - Auto-complete using vector similarity
4. **Enhanced AI Chat** - Chat interface leveraging vector context

All backend APIs are documented and tested. Proceed to Phase 3: Frontend Implementation! 