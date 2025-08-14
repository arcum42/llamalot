# LlamaLot Project - GitHub Copilot Instructions

## Project Overview

LlamaLot is a wxPython-based GUI application for managing and interacting with Ollama models. It provides comprehensive model management, capability detection, and chat functionality through a professional desktop interface.

## Technology Stack

- **GUI Framework**: wxPython 4.2+ (cross-platform desktop GUI)
- **API Integration**: Ollama Python client for model management
- **Database**: SQLite with schema migrations
- **Backend Architecture**: Modular design with separate managers for database, cache, configuration
- **Logging**: Structured logging with file output to `~/.llamalot/logs/`

## Critical Development Environment Rules

### Virtual Environment Requirements
- **ALWAYS activate the virtual environment before any Python operations**
- **NEVER install packages outside the virtual environment**
- **NEVER use system package managers (pacman, apt, yum, etc.) for Python packages**

### Required Commands for Running the Application

```bash
# REQUIRED: Activate virtual environment first
source venv/bin/activate

# REQUIRED: Set PYTHONPATH and run the application
PYTHONPATH=/home/arcum42/Projects/personal/llamalot/src python -m llamalot.main
```

### Dependencies Installation
```bash
# ONLY install dependencies within the virtual environment
source venv/bin/activate
pip install -r requirements.txt
```

## Project Structure

```
├── main.py                    # Application entry point (legacy, use src/llamalot/main.py)
├── requirements.txt           # Python dependencies
├── pyproject.toml            # Project configuration and build settings
├── CHANGELOG.md              # Project changelog and version history
├── README.md                 # Project documentation
├── LICENSE                   # Project license
├── scripts/                  # Development and utility scripts
│   ├── demo_backend.py       # Backend demonstration script
│   └── demo_models.py        # Model management demonstration
├── examples/                 # Usage examples and demonstrations
│   ├── README.md             # Examples documentation
│   └── example_embeddings.py # ChromaDB embeddings usage example
├── tests/                    # Unit tests and test utilities
│   ├── __init__.py           # Test package initialization
│   ├── test_structure.py     # Project structure validation tests
│   ├── test_database.py      # Database functionality tests
│   ├── test_models.py        # Data model tests
│   ├── test_config.py        # Configuration management tests
│   ├── test_ollama_client.py # Ollama client integration tests
│   ├── test_batch_processing.py # Batch processing and wildcard tests
│   ├── test_settings_dialog.py  # Settings dialog functionality tests
│   └── test_embeddings.py   # Embeddings functionality tests
├── test_images/              # Test images for development and testing
│   ├── README.md             # Test images documentation
│   ├── test_batch_image.png  # Batch processing test image
│   ├── test_image.png        # General test image
│   └── test_vision.png       # Vision model test image
├── src/llamalot/             # Main application source code
│   ├── main.py               # Application entry point
│   ├── __init__.py           # Package initialization
│   ├── gui/                  # GUI components and windows
│   │   ├── __init__.py       # GUI package initialization
│   │   ├── main_window.py    # Main application window
│   │   ├── managers/         # Manager classes for application logic
│   │   │   ├── __init__.py   # Managers package initialization
│   │   │   ├── backend_manager.py    # Backend coordination and management
│   │   │   ├── menu_manager.py       # Menu system management
│   │   │   ├── layout_manager.py     # Layout and UI management
│   │   │   └── tab_manager.py        # Tab management system
│   │   ├── tabs/             # Tab implementations for different features
│   │   │   ├── __init__.py   # Tabs package initialization
│   │   │   ├── chat_tab.py   # Chat interface and conversation management
│   │   │   ├── models_tab.py # Model management and information display
│   │   │   ├── batch_tab.py  # Batch processing interface
│   │   │   └── embeddings_tab.py # Embeddings and RAG interface
│   │   ├── components/       # Reusable GUI components
│   │   │   ├── __init__.py   # Components package initialization
│   │   │   ├── batch_processing_panel.py # Batch processing with wildcards
│   │   │   ├── embeddings_chat_panel.py  # Embeddings integration panel
│   │   │   ├── image_attachment_panel.py # Image attachment handling
│   │   │   └── selectable_image_panel.py # Image selection interface
│   │   ├── dialogs/          # Dialog windows for various functions
│   │   │   ├── __init__.py   # Dialogs package initialization
│   │   │   ├── settings_dialog.py       # Application settings configuration
│   │   │   ├── create_model_dialog.py   # Model creation interface
│   │   │   ├── collection_manager_dialog.py # Embeddings collection management
│   │   │   └── document_editor_dialog.py    # Document editing for embeddings
│   │   └── windows/          # Main window implementations
│   │       ├── __init__.py   # Windows package initialization
│   │       └── main_window.py # Enhanced main window implementation
│   ├── backend/              # Backend logic and API integration
│   │   ├── __init__.py       # Backend package initialization
│   │   ├── ollama_client.py  # Ollama API client with timeout configuration
│   │   ├── database.py       # SQLite database management with migrations
│   │   ├── cache.py          # Model caching system
│   │   ├── config.py         # Configuration management and persistence
│   │   ├── embeddings_manager.py # ChromaDB embeddings & RAG functionality
│   │   └── exceptions.py     # Custom exception classes
│   ├── models/               # Data models and configuration classes
│   │   ├── __init__.py       # Models package initialization
│   │   ├── ollama_model.py   # Ollama model representation and capabilities
│   │   ├── config.py         # Application configuration models with validation
│   │   └── chat.py           # Chat conversation and message models
│   └── utils/                # Logging and utility functions
│       ├── __init__.py       # Utils package initialization
│       └── logging_config.py # Centralized logging setup and configuration
└── venv/                     # Virtual environment (not in version control)
```

## Coding Standards

### Testing Requirements
- **ALL new functionality MUST include comprehensive unit tests**
- **Create all tests in the `tests/` directory with descriptive filenames**
- **Test files should follow the pattern `test_<component_name>.py`**
- **Tests must be independent of GUI dependencies when possible**
- **Use proper mocking for external dependencies (Ollama API, file system, etc.)**
- **Include both positive and negative test cases**
- **Test edge cases and error conditions**
- **Run tests with: `source venv/bin/activate && python -m pytest tests/ -v`**

### Version Control Guidelines
- **NEVER add or change version numbers unless explicitly instructed**
- **Version numbers should only be updated for official releases after thorough testing**
- **All version changes must be documented in CHANGELOG.md**
- **Use semantic versioning (MAJOR.MINOR.PATCH) for releases**
- **Development work should not include version bumps**

### Data Models
- Use `@dataclass` for all data models with comprehensive type hints
- Include `Optional`, `List` types as needed
- Follow the established pattern in `ollama_model.py`

### GUI Development with wxPython
- Use proper event binding patterns with `self.Bind()`
- Implement tabbed interfaces with `wx.Notebook` for complex UIs
- **Prefer scrollable panels in notebook tabs** to handle content overflow gracefully
- **Use compact layouts** to maximize screen real estate and improve usability
- Always include error handling and user feedback via `wx.MessageBox`
- Use `wx.CallAfter()` for thread-safe GUI updates

### Backend Integration
- Use individual `/api/show` calls for accurate capability detection
- Use `/api/ps` endpoint for running models detection
- Implement proper error handling for network requests
- Cache model information to reduce API calls

### Logging & Error Handling
- Use centralized logging from `utils.logging_config`
- Include contextual information in log messages
- Implement proper exception handling with user-friendly error messages

### File Editing and Text Encoding
- **AVOID unicode characters, emojis, and special symbols in code when using automated editing tools**
- **Use ASCII-safe text for button labels, comments, and strings during automated edits**
- **If unicode/emoji is needed, implement it manually or use terminal commands**
- Text encoding issues with automated tools can cause file corruption and unexpected behavior
- Prefer plain text labels like "Raw Text" over emoji symbols like "📝 MD"

## Critical Implementation Guidelines

### Model Capability Detection
**CRITICAL**: Always use real API calls for capability detection, not family-based assumptions.

```python
# ✅ CORRECT - Use individual API calls
for model in models:
    capabilities = self.get_model_capabilities(model.name)
    model.capabilities = capabilities

# ❌ INCORRECT - Don't use family-based detection
# Gemma models can have vision capabilities despite family name
```

### GUI Layout Best Practices
1. Use `wx.SplitterWindow` for main/detail views
2. Use `wx.Notebook` for comprehensive information display
3. Enable/disable buttons based on selection state
4. Use visual indicators (●) for running models

### Running Models Detection
- Uses `/api/ps` endpoint to get running models
- Displays running status with bullet indicator (●) in the "Running" column
- Updates automatically when refreshing the model list

## Required Dependencies

```
wxpython>=4.2.0      # GUI framework
ollama>=0.5.3        # Ollama API client  
requests>=2.31.0     # HTTP requests
python-dateutil>=2.8.0  # Date handling
chromadb>=0.4.24     # Vector database for embeddings
markdown>=3.8.0      # Markdown processing for chat export
```

## Development Workflow

1. **Setup**: Activate virtual environment and set PYTHONPATH
2. **Development**: Follow established patterns and coding standards
3. **Testing**: Use the complete run command to verify functionality
4. **Error Handling**: Implement comprehensive error handling and logging

## Key Principles

- Always prioritize user experience and code maintainability
- Use proper thread-safe GUI updates with `wx.CallAfter()`
- Implement comprehensive error handling for all external API calls
- Keep GUI logic separate from backend logic
- Use manager classes for different concerns (Database, Cache, Config)
