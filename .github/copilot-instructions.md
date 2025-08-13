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
src/llamalot/
├── main.py                    # Application entry point
├── gui/windows/enhanced_main_window.py # Main GUI with model management
├── backend/                   # Ollama client, database, cache, config
├── models/                    # Data models and configuration
└── utils/                     # Logging and utilities
```

## Coding Standards

### Data Models
- Use `@dataclass` for all data models with comprehensive type hints
- Include `Optional`, `List` types as needed
- Follow the established pattern in `ollama_model.py`

### GUI Development with wxPython
- Use proper event binding patterns with `self.Bind()`
- Implement tabbed interfaces with `wx.Notebook` for complex UIs
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
