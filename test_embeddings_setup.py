#!/usr/bin/env python3
"""
Test script for embedding functionality.
Tests ChromaDB setup and Ollama embedding integration.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from llamalot.backend.config import ConfigurationManager
from llamalot.backend.embeddings_manager import EmbeddingsManager, Document
from llamalot.backend.ollama_client import OllamaClient

def test_embeddings_setup():
    """Test basic embeddings functionality."""
    print("Testing embeddings setup...")
    
    try:
        # Initialize managers
        config_manager = ConfigurationManager()
        embeddings_manager = EmbeddingsManager(config_manager)
        ollama_client = OllamaClient()
        
        print("✓ Managers initialized successfully")
        
        # Test ChromaDB connection
        collections = embeddings_manager.list_collections()
        print(f"✓ ChromaDB connected. Found {len(collections)} existing collections")
        
        # Test available embedding models
        available_models = embeddings_manager.get_available_embedding_models()
        print(f"✓ Found {len(available_models)} potential embedding models: {available_models}")
        
        # Test Ollama embedding models
        ollama_embedding_models = ollama_client.get_embedding_models()
        print(f"✓ Ollama embedding models: {ollama_embedding_models}")
        
        # Create a test collection
        test_collection = "test_embeddings"
        if test_collection not in collections:
            success = embeddings_manager.create_collection(
                test_collection,
                metadata={"description": "Test collection for embeddings", "created_by": "test_script"}
            )
            print(f"✓ Created test collection: {success}")
        else:
            print(f"✓ Test collection '{test_collection}' already exists")
        
        # Test document creation
        test_docs = [
            Document(
                id="doc1",
                content="Llamas are members of the camelid family.",
                metadata={"source": "test", "type": "fact"}
            ),
            Document(
                id="doc2", 
                content="Llamas were domesticated 4,000 to 5,000 years ago.",
                metadata={"source": "test", "type": "history"}
            )
        ]
        
        print("✓ Test documents created")
        
        # Get collection stats
        stats = embeddings_manager.get_collection_stats(test_collection)
        print(f"✓ Collection stats: {stats}")
        
        print("\n🎉 Embeddings setup test completed successfully!")
        print("\nNext steps:")
        print("1. Install an embedding model: ollama pull mxbai-embed-large")
        print("2. Test embedding generation with actual model")
        print("3. Add documents to collections")
        print("4. Perform similarity searches")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during embeddings setup test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_embedding_model_if_available():
    """Test embedding generation if models are available."""
    print("\nTesting embedding model functionality...")
    
    try:
        config_manager = ConfigurationManager()
        embeddings_manager = EmbeddingsManager(config_manager)
        
        # Try to generate a test embedding
        test_text = "This is a test document for embedding generation."
        
        try:
            embedding = embeddings_manager.generate_embedding(test_text)
            print(f"✓ Generated embedding with {len(embedding)} dimensions")
            
            # Test adding document with embedding
            test_collection = "test_embeddings"
            doc = Document(
                id="embedding_test",
                content=test_text,
                metadata={"test": True}
            )
            
            success = embeddings_manager.add_document(test_collection, doc)
            print(f"✓ Added document with embedding: {success}")
            
            # Test similarity search
            results = embeddings_manager.search_similar(
                test_collection, 
                "test document", 
                n_results=2
            )
            print(f"✓ Similarity search returned {len(results)} results")
            
            for i, result in enumerate(results):
                print(f"  Result {i+1}: Score={result.score:.3f}, Content='{result.document.content[:50]}...'")
            
            return True
            
        except Exception as e:
            print(f"⚠️  Embedding model not available or not working: {e}")
            print("   Install an embedding model with: ollama pull mxbai-embed-large")
            return False
            
    except Exception as e:
        print(f"❌ Error testing embedding model: {e}")
        return False

if __name__ == "__main__":
    print("LlamaLot Embeddings Setup Test")
    print("=" * 40)
    
    # Test basic setup
    setup_success = test_embeddings_setup()
    
    if setup_success:
        # Test embedding functionality if available
        test_embedding_model_if_available()
    
    print("\n" + "=" * 40)
    print("Test completed!")
