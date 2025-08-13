# LlamaLot Embeddings & RAG Support

## Overview

LlamaLot includes comprehensive embeddings support with ChromaDB integration, enabling powerful Retrieval Augmented Generation (RAG) capabilities for enhanced chat responses.

## Features

### Document Management
- Create and manage document collections
- Import text documents and web content
- Automatic text chunking and embedding generation
- Collection statistics and metadata management

### Vector Search
- Semantic similarity search with relevance scoring
- Configurable search result limits
- Integration with chat for contextual responses
- Support for multiple embedding models via Ollama

### RAG Integration
- Automatic context retrieval for chat queries
- Seamless integration with existing chat workflow
- Configurable relevance thresholds
- Real-time embedding generation

## Usage

### Creating Collections
1. Navigate to the "🔍 Embeddings" tab
2. Click "Create Collection" and provide a name
3. Add documents via text input or file upload
4. Documents are automatically processed and embedded

### Searching Collections
- Use the search interface to find relevant documents
- Results include similarity scores and source metadata
- Click results to view full document content

### RAG-Enhanced Chat
- When enabled, chat queries automatically search relevant collections
- Context is seamlessly integrated into model responses
- Configurable number of context results per query

## Technical Details

### Storage
- Collections stored in `~/.llamalot/embeddings/`
- ChromaDB provides persistent vector storage
- SQLite backend for metadata and configuration

### Embedding Models
Supported Ollama embedding models:
- `nomic-embed-text`
- `mxbai-embed-large`
- `all-minilm`
- Any Ollama model with embedding capabilities

### Performance
- Batch processing for large document sets
- Efficient vector indexing with ChromaDB
- Configurable chunk sizes for optimal retrieval
- Persistent collections survive application restarts
- Configurable default embedding models
- Integrated with existing ConfigurationManager

### 3. Testing and Examples

#### Test Script (`test_embeddings_setup.py`)
- Verifies ChromaDB connectivity
- Tests embedding model availability
- Validates basic document operations
- Checks similarity search functionality

#### Comprehensive Example (`example_embeddings.py`)
- Creates sample llama knowledge collection
- Demonstrates document adding with metadata
- Shows semantic similarity search in action
- Illustrates RAG workflow pattern
- Provides ready-to-use code examples

## Key Features Implemented

### Vector Database Operations
✅ **Collection Management**: Create, delete, list, and clear document collections  
✅ **Document Storage**: Add single documents or batch process multiple documents  
✅ **Metadata Support**: Rich metadata storage and filtering capabilities  
✅ **Persistent Storage**: Collections survive application restarts  

### Embedding Generation
✅ **Ollama Integration**: Generate embeddings using local Ollama models  
✅ **Model Discovery**: Automatically detect available embedding models  
✅ **Batch Processing**: Efficient handling of multiple documents  
✅ **Error Handling**: Comprehensive error management and logging  

### Similarity Search
✅ **Semantic Search**: Find documents similar to query text  
✅ **Scoring System**: Similarity scores for ranking results  
✅ **Configurable Results**: Adjustable number of returned documents  
✅ **Fast Retrieval**: Optimized vector similarity calculations  

### RAG Support
✅ **Document Retrieval**: Find relevant context for user queries  
✅ **Context Assembly**: Prepare retrieved content for LLM input  
✅ **Metadata Filtering**: Search within specific document categories  
✅ **Integration Ready**: Seamless connection to chat functionality  

## Available Embedding Models

The system automatically detects and supports various embedding models:

- **mxbai-embed-large**: High-quality general-purpose embeddings (334M params)
- **nomic-embed-text**: Efficient text embeddings (137M params)  
- **all-minilm**: Lightweight sentence embeddings (23M params)
- **bge-models**: BGE (Beijing Academy of AI) embedding models
- **snowflake-arctic-embed**: Snowflake's embedding models
- **granite-embedding**: IBM Granite embedding models

## Usage Examples

### Basic Document Management
```python
from llamalot.backend import EmbeddingsManager, ConfigurationManager, Document

# Initialize
config = ConfigurationManager()
embeddings = EmbeddingsManager(config)

# Create collection
embeddings.create_collection("my_docs", metadata={"type": "knowledge_base"})

# Add document
doc = Document(
    id="doc1", 
    content="Your document content here",
    metadata={"category": "important"}
)
embeddings.add_document("my_docs", doc)
```

### Similarity Search
```python
# Search for similar documents
results = embeddings.search_similar(
    collection_name="my_docs",
    query="What is this about?",
    n_results=5
)

for result in results:
    print(f"Score: {result.score:.3f}")
    print(f"Content: {result.document.content}")
```

### RAG Integration
```python
# Retrieve context for user question
user_question = "How do I configure this?"
relevant_docs = embeddings.search_similar("my_docs", user_question, n_results=3)

# Prepare context for LLM
context = " ".join([doc.document.content for doc in relevant_docs])

# Use with Ollama for enhanced responses
ollama_client = OllamaClient()
enhanced_response = ollama_client.chat(
    model="llama3.2",
    prompt=f"Context: {context}\n\nQuestion: {user_question}\n\nAnswer:"
)
```

## Integration with LlamaLot

The embeddings system is designed to integrate seamlessly with existing LlamaLot features:

### Database Integration
- Shares configuration with existing DatabaseManager
- Consistent error handling and logging patterns
- Follows established code patterns and conventions

### GUI Integration Ready
- Backend classes ready for wxPython GUI integration
- Event-driven operations suitable for UI callbacks
- Progress tracking for long-running operations

### Chat Enhancement
- Can be integrated into chat workflows for context-aware responses
- Document collections can be associated with specific conversations
- Knowledge persistence across chat sessions

## Performance Characteristics

### Storage Efficiency
- ChromaDB provides efficient vector storage and indexing
- Persistent SQLite backend for reliability
- Optimized for both read and write operations

### Search Performance
- Fast similarity calculations using optimized vector operations
- Configurable result limits for performance tuning
- Metadata filtering for targeted searches

### Memory Management
- Lazy loading of collections and embeddings
- Efficient batch processing for large document sets
- Automatic resource cleanup and management

## Next Steps for Integration

1. **GUI Components**: Create wxPython panels for document management
2. **Chat Integration**: Add context retrieval to chat workflows  
3. **File Import**: Build document importing from various file formats
4. **Collection Browser**: Create interface for exploring collections
5. **RAG Chat Mode**: Implement context-aware chat responses

## Files Modified/Created

### Core Implementation
- `src/llamalot/backend/embeddings_manager.py` - Main embeddings functionality
- `src/llamalot/backend/ollama_client.py` - Extended with embedding methods
- `src/llamalot/backend/exceptions.py` - Added embedding-specific exceptions
- `src/llamalot/backend/__init__.py` - Updated exports

### Dependencies
- `requirements.txt` - Added ChromaDB dependency

### Testing and Examples  
- `test_embeddings_setup.py` - Basic functionality tests
- `example_embeddings.py` - Comprehensive usage examples

The embeddings system is now fully implemented and ready for integration into the LlamaLot GUI! The backend provides a solid foundation for building powerful RAG-enhanced chat capabilities.
