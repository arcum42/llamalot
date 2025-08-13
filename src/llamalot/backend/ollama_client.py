"""
Ollama API client for LlamaLot application.

Provides a high-level interface to the Ollama API using the ollama-python library.
Integrates with our data models and handles error management.
"""

import logging
from typing import List, Dict, Any, Optional, Iterator, Union, Callable
from datetime import datetime
import asyncio
import threading
import time
import requests
import json

import ollama
from ollama import Client, AsyncClient
from ollama import ResponseError

from llamalot.models import (
    OllamaModel, 
    ChatMessage, 
    ChatConversation, 
    MessageRole,
    OllamaServerConfig
)
from llamalot.utils.logging_config import get_logger

logger = get_logger(__name__)


class OllamaConnectionError(Exception):
    """Exception raised when connection to Ollama server fails."""
    pass


class OllamaModelNotFoundError(Exception):
    """Exception raised when a requested model is not found."""
    pass


class OllamaClient:
    """
    High-level client for interacting with Ollama API.
    
    This class wraps the ollama-python library and provides:
    - Model management (list, show, pull, delete, copy)
    - Chat functionality with streaming support
    - Error handling and logging
    - Integration with our data models
    """
    
    def __init__(self, config: Optional[OllamaServerConfig] = None):
        """
        Initialize the Ollama client.
        
        Args:
            config: Server configuration (defaults to localhost:11434)
        """
        self.config = config or OllamaServerConfig()
        self.client = Client(host=self.config.base_url, timeout=self.config.timeout)
        self.async_client = AsyncClient(host=self.config.base_url, timeout=self.config.timeout)
        
        logger.info(f"Initialized Ollama client for {self.config.base_url}")
    
    def test_connection(self) -> bool:
        """
        Test connection to Ollama server.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to list models as a simple connection test
            self.client.list()
            logger.info("Ollama server connection test successful")
            return True
        except Exception as e:
            logger.error(f"Ollama server connection test failed: {e}")
            return False
    
    def get_model_capabilities(self, model_name: str) -> List[str]:
        """
        Get capabilities for a specific model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            List of capabilities (e.g., ["completion", "vision"])
        """
        try:
            show_response = self.client.show(model_name)
            return show_response.get('capabilities', ['completion'])
        except Exception as e:
            logger.debug(f"Failed to get capabilities for {model_name}: {e}")
            return ['completion']  # Default fallback
    
    def list_models(self) -> List[OllamaModel]:
        """
        Get list of available models from Ollama with capabilities.
        
        Returns:
            List of OllamaModel instances with capabilities populated
            
        Raises:
            OllamaConnectionError: If connection to server fails
        """
        try:
            logger.debug("Fetching model list from Ollama")
            response = self.client.list()
            
            models = []
            for model_data in response.get('models', []):
                try:
                    # Create basic model from list response
                    model = OllamaModel.from_list_response(model_data)
                    
                    # Fetch actual capabilities from model info
                    try:
                        capabilities = self.get_model_capabilities(model.name)
                        model.capabilities = capabilities
                        logger.debug(f"Loaded model: {model.name} with capabilities: {capabilities}")
                    except Exception as e:
                        logger.debug(f"Failed to get capabilities for {model.name}, using default: {e}")
                        # Keep the capabilities detected from families as fallback
                    
                    models.append(model)
                except ValueError as e:
                    # This catches models with empty names - log at debug level since it's expected
                    if "empty or invalid name" in str(e):
                        logger.debug(f"Skipping model with invalid name: {e}")
                    else:
                        logger.warning(f"Failed to parse model data: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"Failed to parse model data: {e}")
                    continue
            
            logger.info(f"Successfully loaded {len(models)} models")
            return models
            
        except ResponseError as e:
            logger.error(f"Ollama API error while listing models: {e}")
            raise OllamaConnectionError(f"Failed to connect to Ollama server: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while listing models: {e}")
            raise OllamaConnectionError(f"Unexpected error: {e}")
    
    def list_models_basic(self) -> List[OllamaModel]:
        """
        Get basic list of available models from Ollama without capabilities.
        
        This method only fetches the basic model information (name, size, digest, modified_at)
        without making individual API calls for capabilities. Use this for efficient model
        list refreshing when detailed info is not needed.
        
        Returns:
            List of OllamaModel instances with basic information only
            
        Raises:
            OllamaConnectionError: If connection to server fails
        """
        try:
            logger.debug("Fetching basic model list from Ollama")
            response = self.client.list()
            
            models = []
            for model_data in response.get('models', []):
                try:
                    # Create basic model from list response
                    model = OllamaModel.from_list_response(model_data)
                    # Don't fetch capabilities - leave them empty for now
                    models.append(model)
                except ValueError as e:
                    # This catches models with empty names - log at debug level since it's expected
                    if "empty or invalid name" in str(e):
                        logger.debug(f"Skipping model with invalid name: {e}")
                    else:
                        logger.warning(f"Failed to parse model data: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"Failed to parse model data: {e}")
                    continue
            
            logger.info(f"Successfully loaded {len(models)} basic models")
            return models
            
        except ResponseError as e:
            logger.error(f"Ollama API error while listing models: {e}")
            raise OllamaConnectionError(f"Failed to connect to Ollama server: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while listing models: {e}")
            raise OllamaConnectionError(f"Unexpected error: {e}")
    
    def get_running_models(self) -> List[str]:
        """
        Get list of currently running models from Ollama.
        
        Returns:
            List of model names that are currently loaded in memory
            
        Raises:
            OllamaConnectionError: If connection to server fails
        """
        try:
            logger.debug("Fetching running models from Ollama")
            # Use requests to call the /api/ps endpoint directly since ollama-python doesn't have this
            response = requests.get(f"{self.config.base_url}/api/ps", timeout=10)
            response.raise_for_status()
            
            data = response.json()
            running_models = []
            
            for model_data in data.get('models', []):
                model_name = model_data.get('name', model_data.get('model', ''))
                if model_name:
                    running_models.append(model_name)
            
            logger.debug(f"Found {len(running_models)} running models: {running_models}")
            return running_models
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error while getting running models: {e}")
            raise OllamaConnectionError(f"Failed to connect to Ollama server: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while getting running models: {e}")
            raise OllamaConnectionError(f"Unexpected error: {e}")
    
    def get_model_info(self, model_name: str) -> OllamaModel:
        """
        Get detailed information about a specific model.
        
        Args:
            model_name: Name of the model (e.g., "llama3:8b")
            
        Returns:
            OllamaModel with detailed information populated
            
        Raises:
            OllamaModelNotFoundError: If model doesn't exist
            OllamaConnectionError: If connection fails
        """
        try:
            logger.debug(f"Fetching detailed info for model: {model_name}")
            
            # First try to get basic info from list (to get size, etc.)
            models = self.list_models()
            base_model = None
            for model in models:
                if model.name == model_name:
                    base_model = model
                    break
            
            if base_model is None:
                raise OllamaModelNotFoundError(f"Model '{model_name}' not found")
            
            # Get detailed information
            show_response = self.client.show(model_name)
            base_model.update_from_show_response(show_response)
            
            logger.info(f"Successfully loaded detailed info for {model_name}")
            return base_model
            
        except ResponseError as e:
            if "not found" in str(e).lower():
                raise OllamaModelNotFoundError(f"Model '{model_name}' not found")
            else:
                logger.error(f"Ollama API error while getting model info: {e}")
                raise OllamaConnectionError(f"Failed to get model info: {e}")
        except OllamaModelNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error while getting model info: {e}")
            raise OllamaConnectionError(f"Unexpected error: {e}")
    
    def pull_model(self, model_name: str, progress_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None, cancellation_checker: Optional[Callable[[], bool]] = None) -> bool:
        """
        Download a model from Ollama library.
        
        Args:
            model_name: Name of model to download (e.g., "llama3:8b")
            progress_callback: Optional callback for progress updates
            cancellation_checker: Optional function that returns True if operation should be cancelled
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            OllamaConnectionError: If connection fails
        """
        try:
            logger.info(f"Starting pull for model: {model_name}")
            
            if progress_callback:
                # Use streaming pull with progress updates
                stream = self.client.pull(model_name, stream=True)
                for chunk in stream:
                    # Check for cancellation before processing each chunk
                    if cancellation_checker and cancellation_checker():
                        logger.info(f"Pull cancelled for model: {model_name}")
                        return False
                    
                    try:
                        progress_callback("downloading", chunk)
                    except Exception as e:
                        logger.warning(f"Progress callback error: {e}")
            else:
                # Simple non-streaming pull
                self.client.pull(model_name, stream=False)
            
            logger.info(f"Successfully pulled model: {model_name}")
            return True
            
        except ResponseError as e:
            logger.error(f"Ollama API error while pulling model: {e}")
            raise OllamaConnectionError(f"Failed to pull model: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while pulling model: {e}")
            raise OllamaConnectionError(f"Unexpected error: {e}")
    
    def delete_model(self, model_name: str) -> bool:
        """
        Delete a model from local storage.
        
        Args:
            model_name: Name of model to delete
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            OllamaModelNotFoundError: If model doesn't exist
            OllamaConnectionError: If connection fails
        """
        try:
            logger.info(f"Deleting model: {model_name}")
            self.client.delete(model_name)
            logger.info(f"Successfully deleted model: {model_name}")
            return True
            
        except ResponseError as e:
            if "not found" in str(e).lower():
                raise OllamaModelNotFoundError(f"Model '{model_name}' not found")
            else:
                logger.error(f"Ollama API error while deleting model: {e}")
                raise OllamaConnectionError(f"Failed to delete model: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while deleting model: {e}")
            raise OllamaConnectionError(f"Unexpected error: {e}")
    
    def copy_model(self, source_name: str, destination_name: str) -> bool:
        """
        Copy a model to a new name.
        
        Args:
            source_name: Name of source model
            destination_name: Name for the copy
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            OllamaModelNotFoundError: If source model doesn't exist
            OllamaConnectionError: If connection fails
        """
        try:
            logger.info(f"Copying model {source_name} to {destination_name}")
            self.client.copy(source_name, destination_name)
            logger.info(f"Successfully copied model")
            return True
            
        except ResponseError as e:
            if "not found" in str(e).lower():
                raise OllamaModelNotFoundError(f"Source model '{source_name}' not found")
            else:
                logger.error(f"Ollama API error while copying model: {e}")
                raise OllamaConnectionError(f"Failed to copy model: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while copying model: {e}")
            raise OllamaConnectionError(f"Unexpected error: {e}")
    
    def create_model(self, model_name: str, modelfile: str, progress_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None) -> bool:
        """
        Create a new model from a Modelfile.
        
        Args:
            model_name: Name for the new model
            modelfile: Contents of the Modelfile
            progress_callback: Optional callback for progress updates
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            OllamaConnectionError: If creation fails
        """
        try:
            logger.info(f"Creating model: {model_name}")
            
            # Parse the modelfile to extract individual components
            parsed = self._parse_modelfile(modelfile)
            
            # Use the ollama client with parsed parameters
            if progress_callback:
                # For streaming, we need to use the raw HTTP API since the client doesn't support progress callbacks
                url = f"{self.config.base_url}/api/create"
                
                payload = {
                    "model": model_name,
                    "stream": True,
                    **parsed  # Include parsed modelfile components
                }
                
                response = requests.post(url, json=payload, stream=True)
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line.decode('utf-8'))
                            status = chunk.get('status', 'creating')
                            progress_callback(status, chunk)
                            
                            # Check if creation is complete
                            if status == 'success':
                                break
                        except (json.JSONDecodeError, UnicodeDecodeError) as e:
                            logger.warning(f"Failed to parse progress line: {e}")
                            continue
            else:
                # Use the high-level client for non-streaming creation
                self.client.create(model_name, **parsed)
            
            logger.info(f"Successfully created model: {model_name}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error while creating model: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    raise OllamaConnectionError(f"Failed to create model: {error_detail.get('error', str(e))}")
                except:
                    raise OllamaConnectionError(f"Failed to create model: {e}")
            else:
                raise OllamaConnectionError(f"Failed to create model: {e}")
        except ResponseError as e:
            logger.error(f"Ollama API error while creating model: {e}")
            raise OllamaConnectionError(f"Failed to create model: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while creating model: {e}")
            raise OllamaConnectionError(f"Unexpected error: {e}")
    
    def _parse_modelfile(self, modelfile: str) -> Dict[str, Any]:
        """
        Parse a Modelfile string into individual parameters for the ollama client.
        
        Args:
            modelfile: Raw Modelfile content
            
        Returns:
            Dictionary of parsed parameters for the ollama client
        """
        parsed = {}
        lines = modelfile.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            if line.startswith('FROM '):
                # Extract the base model
                from_model = line[5:].strip()
                parsed['from_'] = from_model
            elif line.startswith('SYSTEM '):
                # Extract system prompt
                system_prompt = line[7:].strip()
                # Remove quotes if present
                if system_prompt.startswith('"') and system_prompt.endswith('"'):
                    system_prompt = system_prompt[1:-1]
                parsed['system'] = system_prompt
            elif line.startswith('TEMPLATE '):
                # Extract template
                template = line[9:].strip()
                # Remove quotes if present
                if template.startswith('"""') and template.endswith('"""'):
                    template = template[3:-3]
                elif template.startswith('"') and template.endswith('"'):
                    template = template[1:-1]
                parsed['template'] = template
            elif line.startswith('PARAMETER '):
                # Extract parameters
                param_line = line[10:].strip()
                if ' ' in param_line:
                    param_name, param_value = param_line.split(' ', 1)
                    if 'parameters' not in parsed:
                        parsed['parameters'] = {}
                    
                    # Try to convert to appropriate type
                    try:
                        if '.' in param_value:
                            parsed['parameters'][param_name] = float(param_value)
                        else:
                            parsed['parameters'][param_name] = int(param_value)
                    except ValueError:
                        # Keep as string if conversion fails
                        parsed['parameters'][param_name] = param_value
        
        return parsed
    
    def chat(
        self, 
        model_name: str, 
        conversation: ChatConversation, 
        stream_callback: Optional[Callable[[str], None]] = None,
        **options
    ) -> ChatMessage:
        """
        Send a chat message and get response.
        
        Args:
            model_name: Name of the model to chat with
            conversation: ChatConversation with messages
            stream_callback: Optional callback for streaming responses
            **options: Additional options (temperature, top_p, etc.)
            
        Returns:
            ChatMessage with the response
            
        Raises:
            OllamaModelNotFoundError: If model doesn't exist
            OllamaConnectionError: If chat fails
        """
        try:
            messages = conversation.get_messages_for_api()
            logger.debug(f"Starting chat with {model_name}, {len(messages)} messages")
            
            # Prepare options
            ollama_options = {}
            for key, value in options.items():
                if key == 'context_length':
                    ollama_options['num_ctx'] = value
                elif key == 'max_tokens':
                    ollama_options['num_predict'] = value
                else:
                    ollama_options[key] = value
            
            if stream_callback:
                # Stream the response
                return self._chat_stream(model_name, messages, stream_callback, ollama_options)
            else:
                # Get complete response
                response = self.client.chat(
                    model=model_name, 
                    messages=messages, 
                    stream=False,
                    options=ollama_options if ollama_options else None
                )
                
                # Extract message from response
                message_data = response.get('message', {})
                return ChatMessage(
                    role=MessageRole(message_data.get('role', 'assistant')),
                    content=message_data.get('content', ''),
                    model_name=model_name
                )
                
        except ResponseError as e:
            if "not found" in str(e).lower():
                raise OllamaModelNotFoundError(f"Model '{model_name}' not found")
            else:
                logger.error(f"Ollama API error during chat: {e}")
                raise OllamaConnectionError(f"Chat failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during chat: {e}")
            raise OllamaConnectionError(f"Unexpected chat error: {e}")
    
    def _chat_stream(
        self, 
        model_name: str, 
        messages: List[Dict[str, Any]], 
        callback: Callable[[str], None],
        options: Dict[str, Any]
    ) -> ChatMessage:
        """
        Internal method for streaming chat responses.
        
        Args:
            model_name: Name of the model to chat with
            messages: List of messages in API format
            callback: Callback function for response chunks
            options: Chat options
            
        Returns:
            Complete ChatMessage after streaming
        """
        try:
            full_content = ""
            
            for chunk in self.client.chat(
                model=model_name, 
                messages=messages, 
                stream=True,
                options=options if options else None
            ):
                message = chunk.get('message', {})
                content = message.get('content', '')
                
                if content:
                    full_content += content
                    callback(content)
                
                # Check if done
                if chunk.get('done', False):
                    break
            
            return ChatMessage(
                role=MessageRole.ASSISTANT,
                content=full_content,
                model_name=model_name
            )
            
        except Exception as e:
            logger.error(f"Error during streaming chat: {e}")
            raise OllamaConnectionError(f"Streaming chat failed: {e}")
    
    def generate_embeddings(self, model: str, input_text: Union[str, List[str]], 
                           truncate: bool = True, options: Optional[Dict[str, Any]] = None,
                           keep_alive: str = "5m") -> Dict[str, Any]:
        """
        Generate embeddings for text using specified model.
        
        Args:
            model: Name of the embedding model
            input_text: Text or list of texts to generate embeddings for
            truncate: Whether to truncate text to fit context length
            options: Additional model parameters
            keep_alive: How long to keep model loaded
            
        Returns:
            Dictionary containing embeddings and metadata
            
        Raises:
            OllamaConnectionError: If the request fails
            OllamaModelNotFoundError: If the model is not found
        """
        try:
            logger.debug(f"Generating embeddings with {model}")
            
            if isinstance(input_text, str):
                api_input = input_text
            else:
                api_input = input_text
            
            response = self.client.embed(
                model=model,
                input=api_input,
                truncate=truncate,
                options=options or {},
                keep_alive=keep_alive
            )
            
            # Convert response to dict format for consistency
            result = {
                'model': getattr(response, 'model', model),
                'embeddings': getattr(response, 'embeddings', []),
                'total_duration': getattr(response, 'total_duration', 0),
                'load_duration': getattr(response, 'load_duration', 0),
                'prompt_eval_count': getattr(response, 'prompt_eval_count', 0)
            }
            
            logger.debug(f"Generated embeddings for {len(input_text) if isinstance(input_text, list) else 1} input(s)")
            return result
            
        except ResponseError as e:
            if "not found" in str(e).lower():
                raise OllamaModelNotFoundError(f"Model '{model}' not found")
            else:
                logger.error(f"Ollama API error while generating embeddings: {e}")
                raise OllamaConnectionError(f"Failed to generate embeddings: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while generating embeddings: {e}")
            raise OllamaConnectionError(f"Unexpected embedding error: {e}")
    
    def list_running_models(self) -> List[Dict[str, Any]]:
        """
        Get list of currently running models.
        
        Returns:
            List of running model information
            
        Raises:
            OllamaConnectionError: If connection fails
        """
        try:
            logger.debug("Fetching running models")
            response = self.client.ps()
            models = response.get('models', [])
            logger.debug(f"Found {len(models)} running models")
            return models
            
        except ResponseError as e:
            logger.error(f"Ollama API error while listing running models: {e}")
            raise OllamaConnectionError(f"Failed to list running models: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while listing running models: {e}")
            raise OllamaConnectionError(f"Unexpected error: {e}")

    def get_modelfile(self, model_name: str) -> str:
        """
        Get the modelfile content for a specific model.
        
        Args:
            model_name: Name of the model to get modelfile for
            
        Returns:
            Modelfile content as string
            
        Raises:
            OllamaModelNotFoundError: If model doesn't exist
            OllamaConnectionError: If request fails
        """
        try:
            logger.debug(f"Fetching modelfile for {model_name}")
            response = self.client.show(model_name)
            
            # Extract modelfile from response
            modelfile = response.get('modelfile', '')
            
            if not modelfile:
                logger.warning(f"No modelfile found for {model_name}")
                return f"# No modelfile content available for {model_name}\n# This model may not have a custom modelfile."
            
            logger.debug(f"Successfully retrieved modelfile for {model_name}")
            return modelfile
            
        except ResponseError as e:
            if "not found" in str(e).lower():
                raise OllamaModelNotFoundError(f"Model '{model_name}' not found")
            else:
                logger.error(f"Ollama API error while fetching modelfile for {model_name}: {e}")
                raise OllamaConnectionError(f"Failed to get modelfile: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while fetching modelfile for {model_name}: {e}")
            raise OllamaConnectionError(f"Unexpected error: {e}")
    
    def update_config(self, config: OllamaServerConfig) -> None:
        """
        Update the server configuration.
        
        Args:
            config: New server configuration
        """
        self.config = config
        self.client = Client(host=self.config.base_url, timeout=self.config.timeout)
        self.async_client = AsyncClient(host=self.config.base_url, timeout=self.config.timeout)
        logger.info(f"Updated Ollama client configuration to {self.config.base_url}")
    
    def chat_with_image(
        self, 
        model_name: str, 
        prompt: str, 
        image
    ) -> str:
        """
        Send a prompt with an image to a vision model and get response.
        
        Args:
            model_name: Name of the vision model
            prompt: Text prompt to send with the image
            image: ChatImage containing the image data
            
        Returns:
            String response from the model
            
        Raises:
            OllamaModelNotFoundError: If model doesn't exist
            OllamaConnectionError: If chat fails
        """
        # Set up extended timeout for vision models at the start
        # Use minimum 180 seconds for large models (12B+ parameters) to handle server load
        vision_timeout = max(180, self.config.timeout * 4)  # At least 180 seconds or 4x normal timeout
        
        try:
            logger.info(f"Starting chat_with_image with model: {model_name}")
            logger.debug(f"Prompt length: {len(prompt)} characters")
            logger.debug(f"Image filename: {getattr(image, 'filename', 'unknown')}")
            logger.debug(f"Image size: {getattr(image, 'size_human_readable', 'unknown')}")
            
            # Create the message with image for the API
            messages = [
                {
                    "role": "user",
                    "content": prompt,
                    "images": [image.data]  # Send base64 image data
                }
            ]
            
            logger.debug(f"Sending request to Ollama with {len(messages)} messages")
            
            # Create a temporary client with longer timeout for vision models
            # Vision models typically need more time to process images
            vision_client = Client(host=self.config.base_url, timeout=vision_timeout)
            
            logger.info(f"Using extended timeout of {vision_timeout}s for vision model (model: {model_name})")
            
            # Call Ollama API with the extended timeout client
            response = vision_client.chat(
                model=model_name,
                messages=messages
            )
            
            logger.info(f"Successfully received response from {model_name}")
            response_content = response['message']['content']
            logger.debug(f"Response length: {len(response_content)} characters")
            
            return response_content
            
        except ResponseError as e:
            logger.error(f"Ollama ResponseError in chat_with_image: {e}")
            if "not found" in str(e).lower():
                raise OllamaModelNotFoundError(f"Model '{model_name}' not found")
            else:
                raise OllamaConnectionError(f"Failed to chat with image: {e}") from e
        except requests.exceptions.Timeout as e:
            logger.error(f"Request timeout in chat_with_image after {vision_timeout}s: {e}")
            logger.error(f"Model '{model_name}' may require more processing time for large images or during server load")
            raise OllamaConnectionError(f"Request timed out after {vision_timeout}s - try again or use a smaller/faster model") from e
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error in chat_with_image: {e}")
            raise OllamaConnectionError(f"Failed to connect to Ollama server: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error in chat_with_image: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            # Provide more context for common issues
            if "500" in str(e) and "image" in str(e).lower():
                raise OllamaConnectionError(f"Server error processing image with {model_name}: {e}") from e
            else:
                raise OllamaConnectionError(f"Failed to chat with image: {e}") from e

    def get_embedding_models(self) -> List[str]:
        """
        Get list of models that support embedding generation.
        
        Returns:
            List of embedding model names
        """
        try:
            models = self.list_models()
            
            # Filter for models that support embeddings
            # Common embedding model patterns
            embedding_patterns = [
                'embed', 'embedding', 'minilm', 'sentence', 'mxbai', 'nomic',
                'bge', 'e5', 'instructor', 'gte'
            ]
            
            embedding_models = []
            for model in models:
                model_name = model.name.lower()
                if any(pattern in model_name for pattern in embedding_patterns):
                    embedding_models.append(model.name)
            
            # Add known embedding models that might not match patterns
            known_embedding_models = [
                "mxbai-embed-large", "nomic-embed-text", "all-minilm"
            ]
            
            for known_model in known_embedding_models:
                if known_model not in [m.name for m in models]:
                    # Model not installed, but still list it as available for pulling
                    continue
                if known_model not in embedding_models:
                    embedding_models.append(known_model)
            
            return embedding_models
            
        except Exception as e:
            logger.error(f"Error getting embedding models: {e}")
            return []

    def test_embedding_model(self, model: str) -> bool:
        """
        Test if a model supports embedding generation.
        
        Args:
            model: Model name to test
            
        Returns:
            True if model supports embeddings, False otherwise
        """
        try:
            # Try to generate a simple embedding
            test_response = self.generate_embeddings(
                model=model,
                input_text="test embedding",
                keep_alive="30s"
            )
            
            # Check if we got valid embeddings
            embeddings = test_response.get('embeddings', [])
            if embeddings and len(embeddings) > 0:
                logger.info(f"Model '{model}' supports embeddings")
                return True
            else:
                logger.warning(f"Model '{model}' does not return valid embeddings")
                return False
                
        except Exception as e:
            logger.warning(f"Model '{model}' does not support embeddings: {e}")
            return False

    def __str__(self) -> str:
        """String representation of the client."""
        return f"OllamaClient(host={self.config.base_url})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"OllamaClient(config={self.config})"
