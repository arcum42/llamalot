# LlamaLot

A comprehensive wxPython-based GUI application for managing and interacting with Ollama models, featuring advanced chat capabilities, conversation history, and intelligent model management.

## Features

### 🎯 Core Functionality

- **Model Management**: List, install, delete, and get detailed information about Ollama models
- **Interactive Chat Interface**: Real-time streaming chat with any loaded model
- **Vision Support**: Full image analysis capabilities for vision models (LLaVA, Llama 3.2 Vision, etc.)
- **Model Creation**: Built-in Modelfile editor with syntax highlighting and model creation wizard

### 💬 Advanced Chat Features

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
# From the project directory
python main.py

# Or if installed
llamalot
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
│       │   └── windows/         # Main windows and dialogs
│       ├── backend/             # Backend logic
│       │   ├── ollama_client.py # Ollama API client
│       │   ├── database.py      # Local database operations
│       │   ├── cache.py         # Model caching system
│       │   └── config.py        # Configuration management
│       ├── models/              # Data models
│       │   ├── ollama_model.py  # Ollama model representation
│       │   └── application_config.py # App configuration models
│       └── utils/               # Utilities
│           ├── logging_config.py # Logging setup
│           └── helpers.py       # Helper functions
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
