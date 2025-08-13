# LlamaLot

A comprehensive wxPython-based GUI application for managing and interacting with Ollama models, featuring advanced chat capabilities, conversation history, and intelligent model management.

## Features

### 🔍 Embeddings & RAG Support

- **Document Collections**: Create and manage ChromaDB collections for semantic search
- **RAG Integration**: Retrieve relevant context for chat conversations
- **Vector Search**: Semantic similarity search across document collections
- **Multiple Embedding Models**: Support for various Ollama embedding models
- **Persistent Storage**: Local ChromaDB storage with collection management

### 🎯 Core Functionality

- **Model Management**: List, install, delete, and get detailed information about Ollama models
- **Interactive Chat Interface**: Real-time streaming chat with any loaded model
- **Vision Support**: Full image analysis capabilities for vision models (LLaVA, Llama 3.2 Vision, etc.)
- **Model Creation**: Built-in Modelfile editor with syntax highlighting and model creation wizard

### �️ Advanced Batch Processing

- **Multi-Image Processing**: Process multiple images with vision models simultaneously
- **File Suffix Support**: Flexible file naming with read/write suffixes (e.g., `_tags`, `_desc`)
- **Smart Wildcard System**: Use `%description%` to read existing file content in prompts
- **Selectable Image Management**: Visual thumbnail selection with bulk operations
- **Progress Tracking**: Real-time progress feedback during batch operations
- **Flexible Output Options**: Choose to overwrite existing files or append new content

### �💬 Advanced Chat Features

- **Chat History**: Automatic conversation saving with intelligent title generation
- **AI-Powered Titles**: Smart conversation titles using AI analysis (configurable)
- **New Chat Management**: Easy conversation switching with auto-save
- **Message Threading**: Non-blocking UI with streaming response support
- **Image Attachments**: Multi-image support with preview and clipboard integration

### 🗂️ Data Management

- **SQLite Database**: Local caching for models, conversations, and application state
- **Conversation Search**: Browse and manage chat history with deletion capabilities
- **Configuration System**: Comprehensive settings with UI preferences and chat defaults
- **Export/Import**: Save and share conversations (planned)

### 🎨 User Experience

- **Tabbed Interface**: Organized chat, batch processing, and history views
- **Responsive Design**: Async operations prevent UI freezing during model operations
- **Column Sorting**: Clickable headers for model list organization
- **Progress Tracking**: Visual feedback for model downloads and operations
- **Error Handling**: User-friendly error messages and logging

### 🔧 Technical Features

- **Modular Architecture**: Clean separation with manager classes (Backend, Menu, Layout, Tab)
- **Background Processing**: Non-blocking model operations and chat streaming
- **Memory Management**: Efficient handling of large models and conversations
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Extensible Architecture**: Modular design for easy feature additions

## Prerequisites

- Python 3.8 or higher
- [Ollama](https://ollama.com/download) installed and running
- At least one Ollama model installed (e.g., `ollama pull llama3`)

## Installation

### From Source

1. Clone the repository:

```bash
git clone https://github.com/arcum42/llamalot.git
cd llamalot
```

2. Create a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Install the package in development mode:

```bash
pip install -e .
```

### Using pip (when published)

```bash
pip install llamalot
```

## Usage

### Running the Application

```bash
# From the project directory with virtual environment activated
source venv/bin/activate  # On Windows: venv\Scripts\activate
PYTHONPATH=/home/arcum42/Projects/personal/llamalot/src python -m llamalot.main

# Or using the entry point script
python main.py
```

### Configuration

The application stores its configuration and logs in:

- Linux/macOS: `~/.llamalot/`
- Windows: `%USERPROFILE%\.llamalot\`

### Managing Chat History

LlamaLot automatically saves all your conversations with intelligent features:

#### 📚 Viewing Chat History

1. **Access History**: Click the "📚 History" tab in the main interface
2. **Browse Conversations**: View all past conversations with titles, models used, and timestamps
3. **Select Conversations**: Click any conversation to view the full chat content
4. **Smart Titles**: Conversations get intelligent titles like "Python list comprehensions - 2025-08-08"

#### 💬 Managing Conversations

- **Auto-Save**: Conversations are automatically saved after each message exchange
- **New Chat**: Click "New Chat" button to start fresh (auto-saves current conversation)
- **Model Switching**: Switching models automatically saves the current conversation
- **Delete Conversations**: Select any conversation and click "Delete" (with confirmation)

#### 🤖 AI-Powered Titles

- **Smart Naming**: For longer conversations (4+ messages), AI generates descriptive titles
- **Configurable**: Enable/disable in Settings → "Use AI-generated conversation titles"  
- **Fallback**: Short conversations use cleaned first message + date

### Batch Image Processing

LlamaLot includes a powerful batch processing system for analyzing multiple images:

#### 🔧 Setting Up Batch Processing

1. **Navigate to Batch Tab**: Click the "🖼️ Batch" tab in the main interface
2. **Select Vision Model**: Choose a model with vision capabilities from the dropdown
3. **Add Images**: Click "Add Images" to select multiple image files
4. **Configure Prompt**: Enter your analysis prompt with optional wildcards

#### 📝 Using Wildcards and File Suffixes

- **`%description%` Wildcard**: Includes content from existing text files
- **Read Suffix**: Specify suffix for files to read (e.g., `_tags` reads from `image1_tags.txt`)
- **Write Suffix**: Specify suffix for output files (e.g., `_desc` writes to `image1_desc.txt`)

#### 💡 Example Workflows

**Workflow 1: Basic Description Generation**
- Images: `photo1.jpg`, `photo2.jpg`
- Prompt: `"Describe this image in detail"`
- Write Suffix: `_description`
- Result: Creates `photo1_description.txt`, `photo2_description.txt`

**Workflow 2: Enhanced Analysis with Existing Tags**
- Images: `photo1.jpg`, `photo2.jpg` 
- Existing files: `photo1_tags.txt`, `photo2_tags.txt`
- Prompt: `"Based on these tags: %description%, write a detailed description"`
- Read Suffix: `_tags`
- Write Suffix: `_enhanced`
- Result: Reads existing tag files, creates enhanced descriptions

### Using Embeddings & RAG

Enhance your chat conversations with contextual document search:

#### 📚 Setting Up Collections

1. **Navigate to Embeddings Tab**: Click "🔍 Embeddings" in the main interface
2. **Create Collection**: Click "Create Collection" and name your document set
3. **Add Documents**: Import text files, paste content, or add web articles
4. **Automatic Processing**: Documents are chunked and embedded automatically

#### 🔍 Using RAG in Chat

1. **Enable Context Search**: Toggle RAG integration in embeddings panel
2. **Start Chatting**: Ask questions related to your document collections
3. **Automatic Enhancement**: Relevant context is automatically retrieved and included
4. **View Sources**: See which documents contributed to each response

### Using Vision Models

LlamaLot supports vision models that can analyze images:

1. **Select a vision model** (models with vision capabilities):
   - `llama3.2-vision:latest`
   - `llava:7b` or other LLaVA variants  
   - `gemma3:12b`
   - Any model with "vision" in its capabilities

2. **Attach images to your chat**:
   - Click the "📎 Attach Images" button
   - Select one or multiple image files (PNG, JPG, GIF, BMP, WebP)
   - Preview attached images before sending
   - Double-click any preview image to view it full-size
   - Right-click on full-size images to copy them to the clipboard (or use Ctrl+C)
   - Remove individual images with the "✕" button

3. **Send messages with images**:
   - Type your question about the image(s)
   - Click "Send" or press Enter
   - The model will analyze the attached images and respond

4. **Supported formats**: PNG, JPEG, GIF, BMP, WebP

### Creating Custom Models

Use the built-in model creation wizard:

1. **Access Creator**: Click "Create Model" button in the model list
2. **Choose Base Model**: Select an existing model as foundation
3. **Edit Modelfile**: Use syntax-highlighted editor with real-time validation
4. **Set Parameters**: Configure temperature, system prompts, and other settings
5. **Create Model**: Monitor progress with real-time status updates

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes and releases.

## Development Credits

LlamaLot was primarily developed through an AI-assisted programming approach, with extensive use of **GitHub Copilot** powered by **Claude 3.5 Sonnet**. This collaborative human-AI development process enabled rapid prototyping, comprehensive feature implementation, and robust error handling. (Okay, yeah, I let the AI write the Readme too. :P )

### AI-Assisted Development Highlights

- **Intelligent Code Generation**: Core application architecture and GUI components
- **Feature Implementation**: Chat history, conversation management, and title generation
- **Error Handling**: Comprehensive exception handling and user feedback systems  
- **Documentation**: API documentation, code comments, and user guides
- **Testing & Debugging**: Automated testing scenarios and bug identification

The combination of human creativity and direction with AI's code generation capabilities resulted in a feature-rich, stable application that might have taken significantly longer to develop using traditional methods alone.

## Development

### Setting up the Development Environment

1. Clone the repository and install dependencies as above

2. Install development dependencies:

```bash
pip install -e ".[dev]"
```

3. Run tests:

```bash
pytest
```

4. Format code:

```bash
black src/ tests/
```

5. Type checking:

```bash
mypy src/
```

### Project Structure

```text
llamalot/
├── .github/                     # GitHub configuration
│   └── copilot-instructions.md # Development guidelines
├── src/
│   └── llamalot/
│       ├── __init__.py
│       ├── main.py              # Application entry point
│       ├── gui/                 # GUI components
│       │   ├── components/      # Reusable GUI components
│       │   ├── dialogs/         # Dialog windows
│       │   ├── managers/        # Manager classes (Backend, Menu, Layout, Tab)
│       │   ├── tabs/            # Tab implementations
│       │   └── windows/         # Main windows (main_window.py)
│       ├── backend/             # Backend logic
│       │   ├── ollama_client.py # Ollama API client
│       │   ├── database.py      # Local database operations
│       │   ├── cache.py         # Model caching system
│       │   ├── config.py        # Configuration management
│       │   └── embeddings_manager.py # Embeddings and RAG support
│       ├── models/              # Data models
│       │   ├── ollama_model.py  # Ollama model representation
│       │   ├── config.py        # Configuration models
│       │   └── chat.py          # Chat conversation models
│       └── utils/               # Utilities
│           └── logging_config.py # Logging setup
├── tests/                       # Test files
├── test_images/                 # Test images for development
├── scripts/                     # Development and demo scripts
├── main.py                      # Main entry point
├── requirements.txt             # Dependencies
├── pyproject.toml              # Modern Python packaging
├── CHANGELOG.md                 # Version history
└── README.md                   # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Useful Ollama Resources

### Documentation

- [Ollama API Reference](https://ollama.readthedocs.io/en/api/)
- [Modelfile Reference](https://ollama.readthedocs.io/en/modelfile/)
- [Quickstart Guide](https://ollama.readthedocs.io/en/quickstart/)
- [Importing Models](https://ollama.readthedocs.io/en/import/)
- [Troubleshooting](https://ollama.readthedocs.io/en/troubleshooting/)
- [FAQ](https://ollama.readthedocs.io/en/faq/)
- [Development Guide](https://ollama.readthedocs.io/en/development/)

### Related Projects

- [Ollama Official Website](https://ollama.com/)
- [Ollama Model Library](https://ollama.com/search)
- [Ollama GitHub](https://github.com/ollama/ollama)
- [Ollama Python Library](https://github.com/ollama/ollama-python)
- [Ollama JavaScript Library](https://github.com/ollama/ollama-js)

## Acknowledgments

- **[Ollama](https://ollama.com/)** for the excellent local LLM platform that makes this application possible
- **[wxPython](https://wxpython.org/)** for the robust cross-platform GUI framework
- **[GitHub Copilot](https://github.com/features/copilot)** and **[Claude 3.5 Sonnet](https://claude.ai/)** for AI-assisted development that accelerated feature implementation
- **The open-source community** for all the amazing tools, libraries, and resources that made this project possible
- **Local LLM enthusiasts** who provide feedback and feature requests to improve the application
