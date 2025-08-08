#!/usr/bin/env python3
"""
Example script demonstrating embeddings functionality with ChromaDB and Ollama.
Shows how to create collections, add documents, and perform similarity searches.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from llamalot.backend.config import ConfigurationManager
from llamalot.backend.embeddings_manager import EmbeddingsManager, Document
from llamalot.backend.ollama_client import OllamaClient

def main():
    """Main example demonstrating embeddings functionality."""
    print("LlamaLot Embeddings Example")
    print("=" * 50)
    
    try:
        # Initialize managers
        config_manager = ConfigurationManager()
        embeddings_manager = EmbeddingsManager(config_manager)
        ollama_client = OllamaClient()
        
        print("✓ Initialized embeddings system")
        
        # Create a collection for llama facts
        collection_name = "llama_knowledge"
        embeddings_manager.create_collection(
            collection_name,
            metadata={
                "description": "Facts and information about llamas",
                "created_by": "example_script",
                "domain": "animals"
            }
        )
        print(f"✓ Created collection: {collection_name}")
        
        # Sample documents about llamas
        documents = [
            Document(
                id="llama_family",
                content="Llamas are members of the camelid family, meaning they're closely related to vicuñas, alpacas, and camels. They belong to the same evolutionary lineage and share many physical characteristics.",
                metadata={"topic": "biology", "category": "family"}
            ),
            Document(
                id="llama_history",
                content="Llamas were first domesticated and used as pack animals 4,000 to 5,000 years ago in the Peruvian highlands by the Inca civilization. They were essential for transportation and trade.",
                metadata={"topic": "history", "category": "domestication"}
            ),
            Document(
                id="llama_size",
                content="Llamas can grow as much as 6 feet tall, though the average llama is between 5 feet 6 inches and 5 feet 9 inches tall. They typically weigh between 280 and 450 pounds.",
                metadata={"topic": "physical", "category": "measurements"}
            ),
            Document(
                id="llama_carrying",
                content="Llamas can carry 25 to 30 percent of their body weight, making them excellent pack animals. A typical llama can carry between 70 to 135 pounds for 8 to 13 miles.",
                metadata={"topic": "physical", "category": "capabilities"}
            ),
            Document(
                id="llama_diet",
                content="Llamas are vegetarians and have very efficient digestive systems. They are ruminants with a three-chambered stomach that allows them to digest tough grasses and plants.",
                metadata={"topic": "biology", "category": "diet"}
            ),
            Document(
                id="llama_lifespan",
                content="Llamas live to be about 20 years old on average, though some only live for 15 years while others can live to be 30 years old. Their lifespan depends on care and environment.",
                metadata={"topic": "biology", "category": "lifespan"}
            ),
            Document(
                id="llama_behavior",
                content="Llamas are generally gentle and curious animals, but they can spit when threatened or annoyed. They communicate through humming, clucking, and body language.",
                metadata={"topic": "behavior", "category": "communication"}
            ),
            Document(
                id="llama_fiber",
                content="Llama fiber is prized for its softness, warmth, and hypoallergenic properties. It's used to make high-quality textiles, though it's not as fine as alpaca fiber.",
                metadata={"topic": "commercial", "category": "fiber"}
            )
        ]
        
        # Add documents to the collection
        print(f"Adding {len(documents)} documents to collection...")
        count = embeddings_manager.add_documents_batch(collection_name, documents)
        print(f"✓ Successfully added {count} documents")
        
        # Get collection statistics
        stats = embeddings_manager.get_collection_stats(collection_name)
        print(f"✓ Collection now contains {stats['document_count']} documents")
        
        # Perform some similarity searches
        print("\n" + "=" * 50)
        print("SIMILARITY SEARCH EXAMPLES")
        print("=" * 50)
        
        queries = [
            "What family do llamas belong to?",
            "How much weight can llamas carry?",
            "What do llamas eat?",
            "How long do llamas live?",
            "How tall are llamas?"
        ]
        
        for query in queries:
            print(f"\nQuery: '{query}'")
            results = embeddings_manager.search_similar(
                collection_name, 
                query, 
                n_results=2
            )
            
            for i, result in enumerate(results, 1):
                print(f"  {i}. Score: {result.score:.3f}")
                print(f"     Content: {result.document.content[:100]}...")
                print(f"     Topic: {result.document.metadata.get('topic', 'unknown')}")
        
        # Demonstrate RAG-style usage
        print("\n" + "=" * 50)
        print("RAG (Retrieval Augmented Generation) EXAMPLE")
        print("=" * 50)
        
        user_question = "How are llamas related to other animals?"
        
        # Step 1: Retrieve relevant documents
        relevant_docs = embeddings_manager.search_similar(
            collection_name,
            user_question,
            n_results=2
        )
        
        print(f"User Question: {user_question}")
        print(f"Retrieved {len(relevant_docs)} relevant documents:")
        
        context = ""
        for i, doc in enumerate(relevant_docs, 1):
            print(f"  {i}. {doc.document.content[:100]}...")
            context += doc.document.content + " "
        
        # Step 2: Generate response using context (simulated here)
        print(f"\nContext for LLM: {context[:200]}...")
        print("\n💡 In a real RAG system, you would now:")
        print("   1. Pass the context and question to your LLM")
        print("   2. Generate a response that combines the retrieved information")
        print("   3. Return a well-informed answer to the user")
        
        print("\n" + "=" * 50)
        print("EXAMPLE COMPLETED SUCCESSFULLY!")
        print("=" * 50)
        
        print("\nWhat you've learned:")
        print("✓ How to create and manage document collections")
        print("✓ How to add documents with metadata")
        print("✓ How to perform semantic similarity searches")
        print("✓ How to implement RAG-style document retrieval")
        print("✓ How the embedding system integrates with ChromaDB")
        
        print(f"\nCollection '{collection_name}' is now ready for use!")
        print("You can use it in your LlamaLot application for enhanced chat capabilities.")
        
    except Exception as e:
        print(f"❌ Error in embeddings example: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Embeddings example completed successfully!")
    else:
        print("\n💥 Embeddings example failed!")
        sys.exit(1)
