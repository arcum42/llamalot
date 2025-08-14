# LlamaLot

A powerful desktop GUI application for managing and chatting with local AI models through Ollama. Features advanced chat capabilities, conversation history, batch image processing, and RAG (Retrieval-Augmented Generation) support.

## Features

- **💬 Interactive Chat**: Real-time conversations with any Ollama model
- **🖼️ Vision Support**: Analyze images with vision models (LLaVA, Llama 3.2 Vision, etc.)
- **📚 Chat History**: Automatic conversation saving with AI-generated titles
- **⚡ Batch Processing**: Process multiple images simultaneously with flexible file handling
- **🔍 RAG Integration**: Enhance conversations with document-based context using ChromaDB
- **🎯 Model Management**: Install, delete, and manage local Ollama models
- **🛠️ Model Creation**: Built-in Modelfile editor for creating custom models
- **🎨 Modern Interface**: Clean, tabbed interface with responsive design

## Prerequisites

- Python 3.8 or higher
- [Ollama](https://ollama.com/download) installed and running
- At least one Ollama model installed (e.g., `ollama pull llama3`)

## Installation

### Quick Install (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/arcum42/llamalot.git
   cd llamalot
   ```

2. **Set up virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Using pip (when published)

```bash
pip install llamalot
```

## Getting Started

### Starting the Application

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the application
PYTHONPATH=/path/to/llamalot/src python -m llamalot.main

# Or use the entry point
python main.py
```

### First Steps

1. **Install an Ollama model** (if you haven't already):
   ```bash
   ollama pull llama3
   ```

2. **Launch LlamaLot** and navigate to the **Chat** tab

3. **Select a model** from the dropdown and start chatting!

## Key Features Guide

### 💬 Chat Interface

- **Real-time conversations** with streaming responses
- **Multi-image support** - attach and analyze multiple images at once
- **Conversation history** - all chats are automatically saved
- **Smart titles** - AI generates descriptive titles for your conversations

### 🖼️ Vision Models

Perfect for image analysis with models like LLaVA and Llama 3.2 Vision:

1. Select a vision-capable model
2. Click "📎 Attach Images" 
3. Choose one or multiple images
4. Ask questions about your images
5. Get detailed analysis and descriptions

### ⚡ Batch Processing

Process multiple images efficiently:

1. Go to the **Batch** tab
2. Select a vision model
3. Add multiple images
4. Use advanced features:
   - **Wildcards**: `%description%` to include existing file content
   - **File suffixes**: Organize input/output files (e.g., `_tags.txt`, `_desc.txt`)
   - **Progress tracking**: Monitor batch processing in real-time

### 🔍 RAG Integration

Enhance conversations with document context:

1. Go to the **Embeddings** tab
2. Create a new document collection
3. Add documents (text files, web content, etc.)
4. Enable RAG in chat for context-aware responses

### 🎯 Model Management

- **Browse models**: See all installed Ollama models with detailed information
- **Install/Delete**: Manage your model library
- **Model status**: See which models are currently running
- **Stop models**: Unload running models to free memory

## Configuration

The application stores its data in:
- **Linux/macOS**: `~/.llamalot/`
- **Windows**: `%USERPROFILE%\.llamalot\`

Access settings through the **File → Settings** menu to configure:
- Default chat model
- AI-generated conversation titles
- Ollama server connection
- Interface preferences

## Common Use Cases

### Academic Research
- Analyze research papers with RAG
- Process multiple document images
- Generate summaries and insights

### Content Creation
- Analyze and describe images
- Generate creative writing prompts
- Batch process visual content

### Development
- Code analysis and review
- Documentation assistance
- Technical image analysis

## Troubleshooting

### Connection Issues
- Ensure Ollama is running: `ollama serve`
- Check if models are installed: `ollama list`
- Verify Ollama is accessible on default port (11434)

### Performance Tips
- Use smaller models for faster responses
- Stop unused models to free memory
- Close unused conversations to reduce database size

## Support & Resources

- **Issue Tracker**: [GitHub Issues](https://github.com/arcum42/llamalot/issues)
- **Ollama Documentation**: [https://ollama.com/](https://ollama.com/)
- **Model Library**: [https://ollama.com/search](https://ollama.com/search)

## Development

Want to contribute? See [DEVELOPMENT.md](DEVELOPMENT.md) for setup instructions, coding standards, and contribution guidelines.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed version history and release notes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **[Ollama](https://ollama.com/)** for the excellent local LLM platform
- **[wxPython](https://wxpython.org/)** for the cross-platform GUI framework
- **[ChromaDB](https://www.trychroma.com/)** for embeddings and vector search
- **The open-source community** for all the amazing tools and libraries
