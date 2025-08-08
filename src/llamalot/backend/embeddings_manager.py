"""
Embeddings manager for handling vector embeddings and ChromaDB operations.
Provides functionality for document storage, retrieval, and semantic search.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

import chromadb
from chromadb.config import Settings
import ollama

from .config import ConfigurationManager
from .exceptions import EmbeddingsError


logger = logging.getLogger(__name__)


@dataclass
class Document:
    """Represents a document with metadata for embedding storage."""
    id: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    embedding: Optional[List[float]] = None


@dataclass
class SearchResult:
    """Represents a search result from vector similarity search."""
    document: Document
    distance: float
    score: float  # 1 - distance for similarity scoring


class EmbeddingsManager:
    """
    Manages vector embeddings using ChromaDB and Ollama embedding models.
    
    Provides functionality for:
    - Document embedding generation
    - Vector storage and retrieval
    - Semantic search across documents
    - Collection management
    """
    
    def __init__(self, config_manager: ConfigurationManager):
        """
        Initialize the embeddings manager.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.client = None
        self.collections = {}
        self._default_embedding_model = "mxbai-embed-large"
        
        # Initialize ChromaDB
        self._initialize_chromadb()
    
    def _initialize_chromadb(self):
        """Initialize ChromaDB client with persistent storage."""
        try:
            # Create embeddings directory in user data folder
            data_dir = Path.home() / ".llamalot"
            embeddings_dir = data_dir / "embeddings"
            embeddings_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize ChromaDB client with persistent storage
            self.client = chromadb.PersistentClient(
                path=str(embeddings_dir),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            logger.info(f"ChromaDB initialized with persistent storage at {embeddings_dir}")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise EmbeddingsError(f"ChromaDB initialization failed: {e}")
    
    def get_available_embedding_models(self) -> List[str]:
        """
        Get list of available embedding models from Ollama.
        
        Returns:
            List of embedding model names
        """
        try:
            # Try to get models from Ollama
            response = ollama.list()
            models = response.get('models', [])
            
            # Filter for embedding models (common embedding model patterns)
            embedding_models = []
            embedding_patterns = [
                'embed', 'embedding', 'minilm', 'sentence', 'mxbai', 'nomic'
            ]
            
            for model in models:
                model_name = model.get('name', '').lower()
                if any(pattern in model_name for pattern in embedding_patterns):
                    embedding_models.append(model['name'])
            
            # Add known good embedding models if not present
            known_models = ["mxbai-embed-large", "nomic-embed-text", "all-minilm"]
            for model in known_models:
                if model not in embedding_models:
                    embedding_models.append(model)
            
            return embedding_models
            
        except Exception as e:
            logger.warning(f"Could not fetch embedding models from Ollama: {e}")
            # Return default known models
            return ["mxbai-embed-large", "nomic-embed-text", "all-minilm"]
    
    def create_collection(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Create a new document collection.
        
        Args:
            name: Collection name
            metadata: Optional collection metadata
            
        Returns:
            True if collection was created successfully
        """
        try:
            if not self.client:
                raise EmbeddingsError("ChromaDB client not initialized")
            
            # Check if collection already exists
            try:
                existing = self.client.get_collection(name)
                logger.warning(f"Collection '{name}' already exists")
                self.collections[name] = existing
                return True
            except Exception:
                # Collection doesn't exist, create it
                pass
            
            collection = self.client.create_collection(
                name=name,
                metadata=metadata or {}
            )
            
            self.collections[name] = collection
            logger.info(f"Created collection '{name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create collection '{name}': {e}")
            raise EmbeddingsError(f"Collection creation failed: {e}")
    
    def delete_collection(self, name: str) -> bool:
        """
        Delete a document collection.
        
        Args:
            name: Collection name
            
        Returns:
            True if collection was deleted successfully
        """
        try:
            if not self.client:
                raise EmbeddingsError("ChromaDB client not initialized")
            
            self.client.delete_collection(name)
            
            if name in self.collections:
                del self.collections[name]
            
            logger.info(f"Deleted collection '{name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete collection '{name}': {e}")
            raise EmbeddingsError(f"Collection deletion failed: {e}")
    
    def list_collections(self) -> List[str]:
        """
        List all available collections.
        
        Returns:
            List of collection names
        """
        try:
            if not self.client:
                return []
            
            collections = self.client.list_collections()
            return [col.name for col in collections]
            
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []
    
    def get_collection(self, name: str):
        """
        Get or load a collection by name.
        
        Args:
            name: Collection name
            
        Returns:
            ChromaDB collection object
        """
        if name in self.collections:
            return self.collections[name]
        
        try:
            if not self.client:
                raise EmbeddingsError("ChromaDB client not initialized")
            
            collection = self.client.get_collection(name)
            self.collections[name] = collection
            return collection
            
        except Exception as e:
            logger.error(f"Failed to get collection '{name}': {e}")
            raise EmbeddingsError(f"Collection '{name}' not found: {e}")
    
    def generate_embedding(self, text: str, model: Optional[str] = None) -> List[float]:
        """
        Generate embedding for given text using Ollama.
        
        Args:
            text: Text to embed
            model: Embedding model name (uses default if not specified)
            
        Returns:
            Vector embedding as list of floats
        """
        try:
            if not text.strip():
                raise EmbeddingsError("Cannot generate embedding for empty text")
            
            embedding_model = model or self._default_embedding_model
            
            response = ollama.embed(
                model=embedding_model,
                input=text
            )
            
            embeddings = response.get('embeddings', [])
            if not embeddings:
                raise EmbeddingsError("No embeddings returned from Ollama")
            
            # Return the first (and typically only) embedding
            return embeddings[0]
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise EmbeddingsError(f"Embedding generation failed: {e}")
    
    def add_document(self, collection_name: str, document: Document, 
                    model: Optional[str] = None) -> bool:
        """
        Add a document to a collection with embedding generation.
        
        Args:
            collection_name: Target collection name
            document: Document to add
            model: Embedding model to use
            
        Returns:
            True if document was added successfully
        """
        try:
            collection = self.get_collection(collection_name)
            
            # Generate embedding if not provided
            if not document.embedding:
                document.embedding = self.generate_embedding(document.content, model)
            
            # Add to ChromaDB
            collection.add(
                ids=[document.id],
                embeddings=[document.embedding],
                documents=[document.content],
                metadatas=[document.metadata or {}]
            )
            
            logger.info(f"Added document '{document.id}' to collection '{collection_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add document to collection '{collection_name}': {e}")
            raise EmbeddingsError(f"Document addition failed: {e}")
    
    def add_documents_batch(self, collection_name: str, documents: List[Document],
                           model: Optional[str] = None) -> int:
        """
        Add multiple documents to a collection in batch.
        
        Args:
            collection_name: Target collection name
            documents: List of documents to add
            model: Embedding model to use
            
        Returns:
            Number of documents successfully added
        """
        try:
            collection = self.get_collection(collection_name)
            
            # Prepare batch data
            ids = []
            embeddings = []
            contents = []
            metadatas = []
            
            for doc in documents:
                # Generate embedding if not provided
                if not doc.embedding:
                    doc.embedding = self.generate_embedding(doc.content, model)
                
                ids.append(doc.id)
                embeddings.append(doc.embedding)
                contents.append(doc.content)
                metadatas.append(doc.metadata or {})
            
            # Add batch to ChromaDB
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=contents,
                metadatas=metadatas
            )
            
            logger.info(f"Added {len(documents)} documents to collection '{collection_name}'")
            return len(documents)
            
        except Exception as e:
            logger.error(f"Failed to add documents batch to collection '{collection_name}': {e}")
            raise EmbeddingsError(f"Batch document addition failed: {e}")
    
    def search_similar(self, collection_name: str, query: str, 
                      n_results: int = 5, model: Optional[str] = None) -> List[SearchResult]:
        """
        Search for documents similar to the query text.
        
        Args:
            collection_name: Collection to search in
            query: Query text
            n_results: Number of results to return
            model: Embedding model to use for query
            
        Returns:
            List of search results ordered by similarity
        """
        try:
            collection = self.get_collection(collection_name)
            
            # Generate query embedding
            query_embedding = self.generate_embedding(query, model)
            
            # Perform similarity search
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Convert to SearchResult objects
            search_results = []
            documents = results.get('documents', [[]])[0]
            metadatas = results.get('metadatas', [[]])[0]
            distances = results.get('distances', [[]])[0]
            ids = results.get('ids', [[]])[0]
            
            for i, (doc_id, content, metadata, distance) in enumerate(
                zip(ids, documents, metadatas, distances)
            ):
                document = Document(
                    id=doc_id,
                    content=content,
                    metadata=metadata
                )
                
                search_result = SearchResult(
                    document=document,
                    distance=distance,
                    score=1.0 - distance  # Convert distance to similarity score
                )
                
                search_results.append(search_result)
            
            logger.info(f"Found {len(search_results)} similar documents in '{collection_name}'")
            return search_results
            
        except Exception as e:
            logger.error(f"Failed to search collection '{collection_name}': {e}")
            raise EmbeddingsError(f"Similarity search failed: {e}")
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Get statistics about a collection.
        
        Args:
            collection_name: Collection name
            
        Returns:
            Dictionary containing collection statistics
        """
        try:
            collection = self.get_collection(collection_name)
            
            # Get collection count
            count = collection.count()
            
            # Get collection metadata
            metadata = collection.metadata or {}
            
            return {
                'name': collection_name,
                'document_count': count,
                'metadata': metadata,
                'created_at': metadata.get('created_at'),
                'description': metadata.get('description')
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats for collection '{collection_name}': {e}")
            return {
                'name': collection_name,
                'document_count': 0,
                'metadata': {},
                'error': str(e)
            }
    
    def delete_document(self, collection_name: str, document_id: str) -> bool:
        """
        Delete a document from a collection.
        
        Args:
            collection_name: Collection name
            document_id: Document ID to delete
            
        Returns:
            True if document was deleted successfully
        """
        try:
            collection = self.get_collection(collection_name)
            
            collection.delete(ids=[document_id])
            
            logger.info(f"Deleted document '{document_id}' from collection '{collection_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document '{document_id}': {e}")
            raise EmbeddingsError(f"Document deletion failed: {e}")
    
    def update_default_model(self, model: str):
        """
        Update the default embedding model.
        
        Args:
            model: New default embedding model name
        """
        self._default_embedding_model = model
        logger.info(f"Updated default embedding model to '{model}'")
    
    def get_default_model(self) -> str:
        """
        Get the current default embedding model.
        
        Returns:
            Default embedding model name
        """
        return self._default_embedding_model
    
    def clear_collection(self, collection_name: str) -> bool:
        """
        Clear all documents from a collection.
        
        Args:
            collection_name: Collection name
            
        Returns:
            True if collection was cleared successfully
        """
        try:
            # Delete and recreate the collection
            collection = self.get_collection(collection_name)
            metadata = collection.metadata
            
            self.delete_collection(collection_name)
            self.create_collection(collection_name, metadata)
            
            logger.info(f"Cleared collection '{collection_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear collection '{collection_name}': {e}")
            raise EmbeddingsError(f"Collection clearing failed: {e}")
    
    def close(self):
        """Clean up resources."""
        try:
            self.collections.clear()
            if self.client:
                # ChromaDB client doesn't need explicit closing
                self.client = None
            logger.info("Embeddings manager closed")
            
        except Exception as e:
            logger.error(f"Error closing embeddings manager: {e}")
