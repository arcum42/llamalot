# Examples Directory

This directory contains example scripts demonstrating various LlamaLot features and functionality.

## Available Examples

### `example_embeddings.py`
Comprehensive example demonstrating embeddings functionality with ChromaDB and Ollama:
- Creating and managing document collections
- Adding documents with metadata
- Performing semantic similarity searches
- Implementing RAG (Retrieval Augmented Generation) patterns

To run this example:
```bash
cd /path/to/llamalot
source venv/bin/activate
PYTHONPATH=src python examples/example_embeddings.py
```

**Prerequisites:**
- Install an embedding model: `ollama pull mxbai-embed-large`
- ChromaDB should be available (installed via requirements.txt)

## Usage

These examples are designed to:
1. Demonstrate key features of LlamaLot
2. Provide starting points for custom implementations
3. Show best practices for using the LlamaLot API
4. Test functionality without the full GUI

## Contributing

When adding new examples:
- Include comprehensive docstrings
- Add error handling and user feedback
- Include prerequisites and setup instructions
- Follow the established patterns for imports and structure
