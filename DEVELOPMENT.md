# LlamaLot Development Guide

This document contains information for developers who want to contribute to or extend LlamaLot.

## Setting up the Development Environment

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

5. Install development dependencies:

```bash
pip install -e ".[dev]"
```

## Running from Source

```bash
# From the project directory with virtual environment activated
source venv/bin/activate  # On Windows: venv\Scripts\activate
PYTHONPATH=/home/arcum42/Projects/personal/llamalot/src python -m llamalot.main

# Or using the entry point script
python main.py
```

## Development Tools

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black src/ tests/
```

### Type Checking

```bash
mypy src/
```

## Project Structure

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
├── examples/                    # Usage examples and demonstrations
├── main.py                      # Main entry point (legacy)
├── requirements.txt             # Dependencies
├── pyproject.toml              # Modern Python packaging
├── CHANGELOG.md                 # Version history
├── DEVELOPMENT.md               # This file
└── README.md                   # User documentation
```

## Development Guidelines

For comprehensive development guidelines, coding standards, and best practices, see [.github/copilot-instructions.md](.github/copilot-instructions.md).

Key points:
- Always use the virtual environment
- All new functionality must include comprehensive unit tests
- Follow established patterns for wxPython GUI development
- Use proper error handling and logging
- Keep GUI logic separate from backend logic

## AI-Assisted Development

LlamaLot was primarily developed through an AI-assisted programming approach, with extensive use of **GitHub Copilot** powered by **Claude 3.5 Sonnet**. This collaborative human-AI development process enabled rapid prototyping, comprehensive feature implementation, and robust error handling.

### AI-Assisted Development Highlights

- **Intelligent Code Generation**: Core application architecture and GUI components
- **Feature Implementation**: Chat history, conversation management, and title generation
- **Error Handling**: Comprehensive exception handling and user feedback systems  
- **Documentation**: API documentation, code comments, and user guides
- **Testing & Debugging**: Automated testing scenarios and bug identification

The combination of human creativity and direction with AI's code generation capabilities resulted in a feature-rich, stable application that might have taken significantly longer to develop using traditional methods alone.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following the coding standards
4. Add comprehensive tests for new functionality
5. Commit your changes (`git commit -m 'Add some amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Technical Architecture

### Backend Components

- **OllamaClient**: Handles all communication with the Ollama API
- **DatabaseManager**: SQLite database operations for conversations and caching
- **CacheManager**: Model information caching to reduce API calls
- **ConfigManager**: Application configuration persistence
- **EmbeddingsManager**: ChromaDB integration for RAG functionality

### GUI Architecture

- **MainWindow**: Primary application window with tabbed interface
- **TabManager**: Handles tab creation and management
- **BackendManager**: Coordinates backend components
- **MenuManager**: Application menu system
- **LayoutManager**: UI layout coordination

### Data Models

- **OllamaModel**: Represents Ollama models with capabilities
- **ChatConversation**: Chat conversation with message history
- **ChatMessage**: Individual chat messages with metadata
- **ApplicationConfig**: Application configuration with validation

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
