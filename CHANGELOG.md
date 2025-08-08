# Changelog

All notable changes to LlamaLot will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

#### 💬 Advanced Chat System

- **Chat History Management**: Complete conversation saving with SQLite database integration
- **Intelligent Title Generation**: AI-powered conversation titles with date formatting
- **New Chat Button**: Easy conversation switching with automatic saving
- **History Tab**: Dedicated interface for browsing, viewing, and deleting conversations
- **Auto-Save Functionality**: Conversations saved after each message, model switch, and app close

#### 🔧 Model Management Enhancements

- **Create Model Dialog**: Full Modelfile editor with syntax highlighting and validation
- **Model Creation Wizard**: Step-by-step model creation with progress tracking
- **Column Sorting**: Clickable headers for model list organization (Name, Size, Modified, Running)
- **Running Status Indicators**: Visual bullets (●) showing active models
- **Async Model Operations**: Non-blocking UI during model downloads and operations

#### 🎨 User Interface Improvements

- **Tabbed Interface**: Organized Chat, Batch Processing, and History views
- **Settings System**: Comprehensive configuration with UI preferences and chat defaults
- **Progress Feedback**: Visual progress bars for model creation and operations
- **Error Handling**: User-friendly error messages and comprehensive logging
- **Responsive Design**: Async operations prevent UI freezing

#### 🖼️ Enhanced Vision Support

- **Comprehensive batch processing interface** with selectable image thumbnails
- **Delete Selected and Clear All buttons** for bulk image management
- **Visual selection feedback** with color-coded thumbnails
- **Enhanced image attachment system** with drag-and-drop support
- **Professional layout** with compact spacing and clean design

#### ⚙️ Technical Improvements

- **Model capability detection** using individual API calls for accuracy
- **Background processing** for all model operations
- **Configuration persistence** with automatic state saving
- **Database schema versioning** for future upgrade compatibility
- **Memory optimization** for handling large models and conversations

### Changed

- **Improved GUI layout** with reduced padding for better space utilization
- **Enhanced model management** with tabbed information display
- **Optimized image thumbnail generation** with proper aspect ratio handling
- **Updated wxPython interface** for modern appearance
- **Conversation management** now uses intelligent title generation instead of generic IDs
- **Model selection** automatically saves current conversation before switching

### Fixed

- **Conversation title display** in history list now shows actual titles instead of IDs
- **Layout artifacts** with circular widgets overlaying text
- **Text truncation issues** in image processing labels
- **TextCtrl containment problems** with proper constraints
- **Floating elements** and excessive padding issues
- **Model creation API errors** with proper Modelfile parameter parsing
- **Memory leaks** in conversation and image handling

### Removed

- **Obsolete individual image remove buttons** (replaced with selection system)
- **Redundant StaticBoxSizer elements** causing visual conflicts
- **Generic conversation titles** (replaced with intelligent naming)

## [0.1.0] - 2025-08-08

### Initial Release

- Initial release of LlamaLot
- Basic model management (list, delete, install)
- Chat interface with streaming support
- Vision model support for image analysis
- Local SQLite caching for model information
- Configuration management
- Comprehensive logging system
- RAG system foundation
- Modelfile editor capabilities

### Security

- Local-only operation with no external data transmission
- Secure handling of model data and user conversations
