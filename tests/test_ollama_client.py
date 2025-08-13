"""
Tests for Ollama client functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import List, Dict, Any

from llamalot.backend.ollama_client import (
    OllamaClient, 
    OllamaConnectionError, 
    OllamaModelNotFoundError
)
from llamalot.models import OllamaModel, ChatMessage, ChatConversation
from llamalot.backend.config import ConfigurationManager


class TestOllamaClient(unittest.TestCase):
    """Test cases for OllamaClient."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock configuration
        self.mock_config = Mock()
        self.mock_config.ollama_server.host = "localhost"
        self.mock_config.ollama_server.port = 11434
        self.mock_config.ollama_server.use_https = False
        self.mock_config.ollama_server.timeout = 180
        
        # Create mock config manager
        self.mock_config_manager = Mock(spec=ConfigurationManager)
        self.mock_config_manager.config = self.mock_config
        
        # Create client instance
        self.client = OllamaClient(self.mock_config_manager)
    
    @patch('llamalot.backend.ollama_client.ollama.Client')
    def test_initialization_with_config_manager(self, mock_ollama_client):
        """Test client initialization with configuration manager."""
        client = OllamaClient(self.mock_config_manager)
        
        mock_ollama_client.assert_called_once_with(host="http://localhost:11434", timeout=30)
        self.assertEqual(client.config_manager, self.mock_config_manager)
    
    @patch('llamalot.backend.ollama_client.ollama.Client')
    def test_initialization_with_custom_params(self, mock_ollama_client):
        """Test client initialization with custom parameters."""
        client = OllamaClient(host="custom.host", port=8080, timeout=60)
        
        mock_ollama_client.assert_called_once_with(host="http://custom.host:8080", timeout=60)
        self.assertIsNone(client.config_manager)
    
    @patch('llamalot.backend.ollama_client.ollama.Client')
    def test_initialization_https(self, mock_ollama_client):
        """Test client initialization with HTTPS."""
        self.mock_config.ollama_server.use_https = True
        
        client = OllamaClient(self.mock_config_manager)
        
        mock_ollama_client.assert_called_once_with(host="https://localhost:11434", timeout=30)
    
    def test_test_connection_success(self):
        """Test successful connection test."""
        self.client._client.list = Mock(return_value={'models': []})
        
        result = self.client.test_connection()
        
        self.assertTrue(result)
        self.client._client.list.assert_called_once()
    
    def test_test_connection_failure(self):
        """Test failed connection test."""
        self.client._client.list = Mock(side_effect=Exception("Connection failed"))
        
        result = self.client.test_connection()
        
        self.assertFalse(result)
    
    def test_list_models_success(self):
        """Test successful model listing."""
        mock_response = {
            'models': [
                {
                    'name': 'llama2:7b',
                    'size': 3800000000,
                    'digest': 'abc123',
                    'modified_at': '2024-01-01T00:00:00Z',
                    'details': {
                        'format': 'gguf',
                        'family': 'llama',
                        'families': ['llama'],
                        'parameter_size': '7B',
                        'quantization_level': 'Q4_0'
                    }
                }
            ]
        }
        
        self.client._client.list = Mock(return_value=mock_response)
        
        models = self.client.list_models()
        
        self.assertEqual(len(models), 1)
        self.assertIsInstance(models[0], OllamaModel)
        self.assertEqual(models[0].name, 'llama2:7b')
        self.assertEqual(models[0].size, 3800000000)
    
    def test_list_models_connection_error(self):
        """Test model listing with connection error."""
        self.client._client.list = Mock(side_effect=Exception("Connection failed"))
        
        with self.assertRaises(OllamaConnectionError):
            self.client.list_models()
    
    def test_get_model_info_success(self):
        """Test successful model info retrieval."""
        mock_response = {
            'modelfile': 'FROM llama2:7b',
            'parameters': 'temperature 0.7',
            'template': '{{ .Prompt }}',
            'details': {
                'format': 'gguf',
                'family': 'llama',
                'families': ['llama'],
                'parameter_size': '7B',
                'quantization_level': 'Q4_0'
            }
        }
        
        self.client._client.show = Mock(return_value=mock_response)
        
        model_info = self.client.get_model_info('llama2:7b')
        
        self.assertIsNotNone(model_info)
        self.assertEqual(model_info.modelfile, 'FROM llama2:7b')
        self.assertEqual(model_info.parameters, 'temperature 0.7')
        self.client._client.show.assert_called_once_with('llama2:7b')
    
    def test_get_model_info_not_found(self):
        """Test model info retrieval for non-existent model."""
        self.client._client.show = Mock(side_effect=Exception("Model not found"))
        
        with self.assertRaises(OllamaModelNotFoundError):
            self.client.get_model_info('nonexistent')
    
    def test_pull_model_success(self):
        """Test successful model pulling."""
        mock_progress_callback = Mock()
        
        # Mock the pull generator
        def mock_pull_generator():
            yield {'status': 'downloading', 'completed': 1000, 'total': 5000}
            yield {'status': 'downloading', 'completed': 3000, 'total': 5000}
            yield {'status': 'success'}
        
        self.client._client.pull = Mock(return_value=mock_pull_generator())
        
        result = self.client.pull_model('llama2:7b', progress_callback=mock_progress_callback)
        
        self.assertTrue(result)
        self.client._client.pull.assert_called_once_with('llama2:7b', stream=True)
        
        # Check progress callback was called
        self.assertGreater(mock_progress_callback.call_count, 0)
    
    def test_delete_model_success(self):
        """Test successful model deletion."""
        self.client._client.delete = Mock(return_value=True)
        
        result = self.client.delete_model('llama2:7b')
        
        self.assertTrue(result)
        self.client._client.delete.assert_called_once_with('llama2:7b')
    
    def test_delete_model_not_found(self):
        """Test model deletion for non-existent model."""
        self.client._client.delete = Mock(side_effect=Exception("Model not found"))
        
        with self.assertRaises(OllamaModelNotFoundError):
            self.client.delete_model('nonexistent')
    
    def test_copy_model_success(self):
        """Test successful model copying."""
        self.client._client.copy = Mock(return_value=True)
        
        result = self.client.copy_model('llama2:7b', 'llama2:7b-backup')
        
        self.assertTrue(result)
        self.client._client.copy.assert_called_once_with('llama2:7b', 'llama2:7b-backup')
    
    def test_create_model_success(self):
        """Test successful model creation."""
        modelfile = "FROM llama2:7b\nSYSTEM You are a helpful assistant."
        
        def mock_create_generator():
            yield {'status': 'reading model metadata'}
            yield {'status': 'creating model layer'}
            yield {'status': 'success'}
        
        self.client._client.create = Mock(return_value=mock_create_generator())
        
        result = self.client.create_model('custom-model', modelfile)
        
        self.assertTrue(result)
        self.client._client.create.assert_called_once_with(
            model='custom-model',
            modelfile=modelfile,
            stream=True
        )
    
    def test_chat_success(self):
        """Test successful chat completion."""
        conversation = ChatConversation()
        conversation.add_message(ChatMessage(role="user", content="Hello!"))
        
        mock_response = {
            'message': {'role': 'assistant', 'content': 'Hello! How can I help you?'},
            'done': True
        }
        
        self.client._client.chat = Mock(return_value=mock_response)
        
        response = self.client.chat('llama2:7b', conversation)
        
        self.assertIsInstance(response, ChatMessage)
        self.assertEqual(response.role, 'assistant')
        self.assertEqual(response.content, 'Hello! How can I help you?')
    
    def test_chat_with_options(self):
        """Test chat with custom options."""
        conversation = ChatConversation()
        conversation.add_message(ChatMessage(role="user", content="Hello!"))
        
        mock_response = {
            'message': {'role': 'assistant', 'content': 'Hello!'},
            'done': True
        }
        
        self.client._client.chat = Mock(return_value=mock_response)
        
        response = self.client.chat(
            'llama2:7b', 
            conversation,
            temperature=0.8,
            context_length=1000
        )
        
        # Verify the client was called with options
        args, kwargs = self.client._client.chat.call_args
        self.assertIn('options', kwargs)
        self.assertEqual(kwargs['options']['temperature'], 0.8)
        self.assertEqual(kwargs['options']['num_ctx'], 1000)
    
    def test_chat_streaming(self):
        """Test streaming chat completion."""
        conversation = ChatConversation()
        conversation.add_message(ChatMessage(role="user", content="Hello!"))
        
        def mock_chat_generator():
            yield {'message': {'role': 'assistant', 'content': 'Hello'}, 'done': False}
            yield {'message': {'role': 'assistant', 'content': '!'}, 'done': False}
            yield {'message': {'role': 'assistant', 'content': ''}, 'done': True}
        
        self.client._client.chat = Mock(return_value=mock_chat_generator())
        
        callback = Mock()
        response = self.client.chat('llama2:7b', conversation, stream_callback=callback)
        
        self.assertIsInstance(response, ChatMessage)
        self.assertEqual(response.content, 'Hello!')
        
        # Verify streaming callback was called
        self.assertGreater(callback.call_count, 0)
    
    def test_generate_embeddings_success(self):
        """Test successful embedding generation."""
        mock_response = {
            'embedding': [0.1, 0.2, 0.3, 0.4, 0.5]
        }
        
        self.client._client.embeddings = Mock(return_value=mock_response)
        
        embeddings = self.client.generate_embeddings('embed-model', 'Test text')
        
        self.assertEqual(embeddings, [0.1, 0.2, 0.3, 0.4, 0.5])
        self.client._client.embeddings.assert_called_once_with(
            model='embed-model',
            prompt='Test text'
        )
    
    def test_generate_embeddings_batch(self):
        """Test batch embedding generation."""
        texts = ['Text 1', 'Text 2', 'Text 3']
        
        # Mock individual embedding responses
        mock_responses = [
            {'embedding': [0.1, 0.2]},
            {'embedding': [0.3, 0.4]},
            {'embedding': [0.5, 0.6]}
        ]
        
        self.client._client.embeddings = Mock(side_effect=mock_responses)
        
        embeddings = self.client.generate_embeddings('embed-model', texts)
        
        self.assertEqual(len(embeddings), 3)
        self.assertEqual(embeddings[0], [0.1, 0.2])
        self.assertEqual(embeddings[1], [0.3, 0.4])
        self.assertEqual(embeddings[2], [0.5, 0.6])
    
    def test_list_running_models_success(self):
        """Test successful listing of running models."""
        mock_response = {
            'models': [
                {
                    'name': 'llama2:7b',
                    'size': 3800000000,
                    'digest': 'abc123',
                    'expires_at': '2024-01-01T01:00:00Z'
                }
            ]
        }
        
        self.client._client.ps = Mock(return_value=mock_response)
        
        models = self.client.list_running_models()
        
        self.assertEqual(len(models), 1)
        self.assertIsInstance(models[0], OllamaModel)
        self.assertEqual(models[0].name, 'llama2:7b')
    
    def test_update_config_success(self):
        """Test successful configuration update."""
        new_config = Mock()
        new_config.ollama_server.host = "newhost"
        new_config.ollama_server.port = 8080
        new_config.ollama_server.use_https = True
        new_config.ollama_server.timeout = 60
        
        with patch('llamalot.backend.ollama_client.ollama.Client') as mock_ollama_client:
            self.client.update_config(new_config)
            
            mock_ollama_client.assert_called_with(host="https://newhost:8080", timeout=60)
    
    def test_context_manager(self):
        """Test client as context manager."""
        with self.client as client:
            self.assertIs(client, self.client)
    
    def test_repr(self):
        """Test string representation."""
        repr_str = repr(self.client)
        self.assertIn("OllamaClient", repr_str)
        self.assertIn("localhost:11434", repr_str)


class TestOllamaClientExceptions(unittest.TestCase):
    """Test cases for Ollama client exception handling."""
    
    def test_ollama_connection_error(self):
        """Test OllamaConnectionError exception."""
        error = OllamaConnectionError("Connection failed")
        self.assertEqual(str(error), "Connection failed")
        self.assertIsInstance(error, Exception)
    
    def test_ollama_model_not_found_error(self):
        """Test OllamaModelNotFoundError exception."""
        error = OllamaModelNotFoundError("Model not found: llama2")
        self.assertEqual(str(error), "Model not found: llama2")
        self.assertIsInstance(error, Exception)


if __name__ == '__main__':
    unittest.main()
