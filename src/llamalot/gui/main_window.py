"""
Main window for LlamaLot application.

Contains the primary GUI interface for managing Ollama models.
"""

import wx
import wx.lib.scrolledpanel as scrolled
import asyncio
import threading
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from pathlib import Path

from llamalot.utils.logging_config import get_logger
from llamalot.backend.ollama_client import OllamaClient
from llamalot.backend.cache import CacheManager
from llamalot.backend.database import DatabaseManager
from llamalot.models import OllamaModel, ChatConversation, ChatMessage, ApplicationConfig
from llamalot.backend.exceptions import OllamaConnectionError, ModelNotFoundError

logger = get_logger(__name__)


class MainWindow(wx.Frame):
    """Main application window with enhanced GUI."""
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__(
            parent=None,
            title="LlamaLot - Ollama Model Manager",
            size=wx.Size(1400, 900)
        )
        
        logger.info("Initializing enhanced main window")
        
        # Set minimum size
        self.SetMinSize(wx.Size(1000, 700))
        
        # Center the window
        self.Center()
        
        # Initialize backend components
        self._init_backend()
        
        # Initialize GUI state
        self.current_model: Optional[OllamaModel] = None
        self.current_conversation: Optional[ChatConversation] = None
        self.models: List[OllamaModel] = []
        self.conversations: List[ChatConversation] = []
        
        # Set up the window icon (if available)
        self._setup_icon()
        
        # Create the menu bar
        self._create_menu_bar()
        
        # Create the status bar
        self._create_status_bar()
        
        # Create the main layout
        self._create_main_layout()
        
        # Bind events
        self._bind_events()
        
        # Load initial data
        self._load_initial_data()
        
        logger.info("Enhanced main window initialized successfully")
    
    def _init_backend(self) -> None:
        """Initialize backend components."""
        try:
            # Initialize configuration
            self.config = ApplicationConfig.load_from_file()
            self.config.ensure_directories()
            
            # Initialize database
            db_path = Path(self.config.database_file)
            self.db_manager = DatabaseManager(db_path)
            
            # Initialize Ollama client
            self.ollama_client = OllamaClient(
                host=self.config.ollama_server.host,
                port=self.config.ollama_server.port,
                timeout=self.config.ollama_server.timeout
            )
            
            # Initialize cache manager
            self.cache_manager = CacheManager(
                self.db_manager,
                self.ollama_client
            )
            
            logger.info("Backend components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize backend: {e}")
            wx.MessageBox(
                f"Failed to initialize backend components:\n{str(e)}", 
                "Initialization Error", 
                wx.OK | wx.ICON_ERROR
            )
    
    def _setup_icon(self) -> None:
        """Set up the application icon."""
        # TODO: Add application icon
        pass
    
    def _create_menu_bar(self) -> None:
        """Create the application menu bar."""
        menubar = wx.MenuBar()
        
        # File menu
        file_menu = wx.Menu()
        file_menu.Append(wx.ID_NEW, "New &Conversation\tCtrl+N", "Start a new conversation")
        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_OPEN, "&Open Conversation\tCtrl+O", "Open saved conversation")
        file_menu.Append(wx.ID_SAVE, "&Save Conversation\tCtrl+S", "Save current conversation")
        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_REFRESH, "&Refresh\tF5", "Refresh model list")
        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_EXIT, "E&xit\tCtrl+Q", "Exit the application")
        menubar.Append(file_menu, "&File")
        
        # Edit menu
        edit_menu = wx.Menu()
        edit_menu.Append(wx.ID_COPY, "&Copy\tCtrl+C", "Copy selected text")
        edit_menu.Append(wx.ID_PASTE, "&Paste\tCtrl+V", "Paste text")
        edit_menu.Append(wx.ID_SELECTALL, "Select &All\tCtrl+A", "Select all text")
        menubar.Append(edit_menu, "&Edit")
        
        # Models menu
        models_menu = wx.Menu()
        models_menu.Append(10001, "&Pull Model\tCtrl+P", "Download a model")
        models_menu.Append(10002, "&Delete Model\tDel", "Delete selected model")
        models_menu.Append(10003, "&Model Info\tCtrl+I", "Show model information")
        models_menu.AppendSeparator()
        models_menu.Append(10004, "&Chat with Model\tCtrl+T", "Start chat with selected model")
        menubar.Append(models_menu, "&Models")
        
        # View menu
        view_menu = wx.Menu()
        view_menu.Append(10005, "Show &Model List\tF2", "Toggle model list panel")
        view_menu.Append(10006, "Show &Conversations\tF3", "Toggle conversations panel")
        view_menu.Append(10007, "Show &Chat\tF4", "Toggle chat panel")
        menubar.Append(view_menu, "&View")
        
        # Help menu
        help_menu = wx.Menu()
        help_menu.Append(wx.ID_ABOUT, "&About\tF1", "About LlamaLot")
        help_menu.Append(10008, "&User Guide", "Open user guide")
        menubar.Append(help_menu, "&Help")
        
        self.SetMenuBar(menubar)
    
    def _create_status_bar(self) -> None:
        """Create the status bar."""
        self.status_bar = self.CreateStatusBar(3)
        self.status_bar.SetStatusWidths([-1, 150, 100])
        self.status_bar.SetStatusText("Ready", 0)
        self.status_bar.SetStatusText("No model selected", 1)
        self.status_bar.SetStatusText("Connected", 2)
    
    def _create_main_layout(self) -> None:
        """Create the main layout with splitter windows."""
        # Create main panel
        self.main_panel = wx.Panel(self)
        
        # Create main splitter (horizontal - left/right)
        self.main_splitter = wx.SplitterWindow(
            self.main_panel, 
            style=wx.SP_3D | wx.SP_LIVE_UPDATE
        )
        self.main_splitter.SetMinimumPaneSize(200)
        
        # Create left panel (models and conversations)
        self.left_panel = wx.Panel(self.main_splitter)
        self._create_left_panel()
        
        # Create right panel (chat interface)
        self.right_panel = wx.Panel(self.main_splitter)
        self._create_right_panel()
        
        # Split the main window
        self.main_splitter.SplitVertically(self.left_panel, self.right_panel, 350)
        
        # Main sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.main_splitter, 1, wx.EXPAND)
        self.main_panel.SetSizer(main_sizer)
    
    def _create_left_panel(self) -> None:
        """Create the left panel with model list and conversations."""
        # Create left splitter (vertical - top/bottom)
        self.left_splitter = wx.SplitterWindow(
            self.left_panel,
            style=wx.SP_3D | wx.SP_LIVE_UPDATE
        )
        self.left_splitter.SetMinimumPaneSize(150)
        
        # Create model list panel
        self.model_panel = wx.Panel(self.left_splitter)
        self._create_model_panel()
        
        # Create conversations panel
        self.conv_panel = wx.Panel(self.left_splitter)
        self._create_conversations_panel()
        
        # Split the left panel
        self.left_splitter.SplitHorizontally(self.model_panel, self.conv_panel, 300)
        
        # Left panel sizer
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        left_sizer.Add(self.left_splitter, 1, wx.EXPAND)
        self.left_panel.SetSizer(left_sizer)
    
    def _create_model_panel(self) -> None:
        """Create the model list panel."""
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Model list header
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        model_label = wx.StaticText(self.model_panel, label="Models")
        model_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        
        # Refresh button
        self.refresh_btn = wx.Button(self.model_panel, label="↻", size=wx.Size(30, 25))
        self.refresh_btn.SetToolTip("Refresh model list")
        
        header_sizer.Add(model_label, 1, wx.ALIGN_CENTER_VERTICAL)
        header_sizer.Add(self.refresh_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        
        # Model list control
        self.model_list = wx.ListCtrl(
            self.model_panel,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES
        )
        
        # Add columns
        self.model_list.AppendColumn("Name", width=150)
        self.model_list.AppendColumn("Size", width=80)
        self.model_list.AppendColumn("Modified", width=100)
        
        # Model info panel
        self.model_info = wx.StaticText(
            self.model_panel,
            label="Select a model to view details",
            style=wx.ST_ELLIPSIZE_END
        )
        
        # Add to sizer
        sizer.Add(header_sizer, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.model_list, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        sizer.Add(self.model_info, 0, wx.EXPAND | wx.ALL, 5)
        
        self.model_panel.SetSizer(sizer)
    
    def _create_conversations_panel(self) -> None:
        """Create the conversations panel."""
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Conversations header
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        conv_label = wx.StaticText(self.conv_panel, label="Conversations")
        conv_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        
        # New conversation button
        self.new_conv_btn = wx.Button(self.conv_panel, label="+", size=wx.Size(30, 25))
        self.new_conv_btn.SetToolTip("New conversation")
        
        header_sizer.Add(conv_label, 1, wx.ALIGN_CENTER_VERTICAL)
        header_sizer.Add(self.new_conv_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        
        # Conversations list
        self.conv_list = wx.ListCtrl(
            self.conv_panel,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES
        )
        
        # Add columns
        self.conv_list.AppendColumn("Title", width=200)
        self.conv_list.AppendColumn("Model", width=120)
        self.conv_list.AppendColumn("Messages", width=60)
        
        # Add to sizer
        sizer.Add(header_sizer, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.conv_list, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        
        self.conv_panel.SetSizer(sizer)
    
    def _create_right_panel(self) -> None:
        """Create the right panel with chat interface."""
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Chat header
        self.chat_header = wx.Panel(self.right_panel)
        self._create_chat_header()
        
        # Chat display area
        self.chat_display = wx.TextCtrl(
            self.right_panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP
        )
        self.chat_display.SetFont(wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        
        # Chat input area
        self.chat_input_panel = wx.Panel(self.right_panel)
        self._create_chat_input()
        
        # Add to sizer
        sizer.Add(self.chat_header, 0, wx.EXPAND)
        sizer.Add(self.chat_display, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
        sizer.Add(self.chat_input_panel, 0, wx.EXPAND)
        
        self.right_panel.SetSizer(sizer)
    
    def _create_chat_header(self) -> None:
        """Create the chat header with model info and controls."""
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Current model info
        self.current_model_label = wx.StaticText(
            self.chat_header,
            label="No model selected"
        )
        self.current_model_label.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        
        # Chat controls
        self.clear_chat_btn = wx.Button(self.chat_header, label="Clear", size=wx.Size(60, 25))
        self.clear_chat_btn.SetToolTip("Clear chat history")
        
        sizer.Add(self.current_model_label, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        sizer.Add(self.clear_chat_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        
        self.chat_header.SetSizer(sizer)
    
    def _create_chat_input(self) -> None:
        """Create the chat input area."""
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Input text control
        self.chat_input = wx.TextCtrl(
            self.chat_input_panel,
            style=wx.TE_MULTILINE | wx.TE_PROCESS_ENTER,
            size=wx.Size(-1, 80)
        )
        self.chat_input.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        
        # Send button
        self.send_btn = wx.Button(self.chat_input_panel, label="Send", size=wx.Size(60, 80))
        self.send_btn.SetToolTip("Send message (Ctrl+Enter)")
        
        sizer.Add(self.chat_input, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.send_btn, 0, wx.ALL, 5)
        
        self.chat_input_panel.SetSizer(sizer)
    
    def _bind_events(self) -> None:
        """Bind event handlers."""
        # Menu events
        self.Bind(wx.EVT_MENU, self.on_exit, id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.on_about, id=wx.ID_ABOUT)
        self.Bind(wx.EVT_MENU, self.on_refresh, id=wx.ID_REFRESH)
        self.Bind(wx.EVT_MENU, self.on_new_conversation, id=wx.ID_NEW)
        
        # Button events
        self.Bind(wx.EVT_BUTTON, self.on_refresh, self.refresh_btn)
        self.Bind(wx.EVT_BUTTON, self.on_new_conversation, self.new_conv_btn)
        self.Bind(wx.EVT_BUTTON, self.on_clear_chat, self.clear_chat_btn)
        self.Bind(wx.EVT_BUTTON, self.on_send_message, self.send_btn)
        
        # List events
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_model_selected, self.model_list)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_conversation_selected, self.conv_list)
        
        # Text events
        self.Bind(wx.EVT_TEXT_ENTER, self.on_chat_input_enter, self.chat_input)
        
        # Window events
        self.Bind(wx.EVT_CLOSE, self.on_close)
    
    def _load_initial_data(self) -> None:
        """Load initial data on startup."""
        wx.CallAfter(self._load_models_async)
        wx.CallAfter(self._load_conversations_async)
    
    def _load_models_async(self) -> None:
        """Load models asynchronously."""
        try:
            self.status_bar.SetStatusText("Loading models...", 0)
            
            # Get models from cache (which will sync with Ollama if needed)
            self.models = self.cache_manager.get_cached_models()
            
            # Update model list
            self._update_model_list()
            
            self.status_bar.SetStatusText("Ready", 0)
            self.status_bar.SetStatusText(f"{len(self.models)} models", 1)
            
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            self.status_bar.SetStatusText("Error loading models", 0)
            wx.MessageBox(
                f"Failed to load models:\n{str(e)}", 
                "Error", 
                wx.OK | wx.ICON_ERROR
            )
    
    def _load_conversations_async(self) -> None:
        """Load conversations asynchronously."""
        try:
            # Get conversations from database
            self.conversations = self.db_manager.list_conversations()
            
            # Update conversations list
            self._update_conversations_list()
            
        except Exception as e:
            logger.error(f"Failed to load conversations: {e}")
            wx.MessageBox(
                f"Failed to load conversations:\n{str(e)}", 
                "Error", 
                wx.OK | wx.ICON_ERROR
            )
    
    def _update_model_list(self) -> None:
        """Update the model list display."""
        self.model_list.DeleteAllItems()
        
        for i, model in enumerate(self.models):
            # Format size
            size_str = self._format_size(model.size)
            
            # Format date
            date_str = model.modified_at.strftime("%m/%d/%y")
            
            # Add to list
            index = self.model_list.InsertItem(i, model.name)
            self.model_list.SetItem(index, 1, size_str)
            self.model_list.SetItem(index, 2, date_str)
    
    def _update_conversations_list(self) -> None:
        """Update the conversations list display."""
        self.conv_list.DeleteAllItems()
        
        for i, conv in enumerate(self.conversations):
            # Get message count
            messages = self.db_manager.get_conversation_messages(conv.conversation_id)
            msg_count = len(messages)
            
            # Add to list
            index = self.conv_list.InsertItem(i, conv.title)
            self.conv_list.SetItem(index, 1, conv.model_name)
            self.conv_list.SetItem(index, 2, str(msg_count))
    
    def _format_size(self, size_bytes: int) -> str:
        """Format size in bytes to human readable string."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}PB"
    
    # Event handlers
    def on_exit(self, event: wx.CommandEvent) -> None:
        """Handle exit menu item."""
        self.Close()
    
    def on_about(self, event: wx.CommandEvent) -> None:
        """Show about dialog."""
        info = wx.adv.AboutDialogInfo()
        info.SetName("LlamaLot")
        info.SetVersion("0.1.0")
        info.SetDescription("A wxPython-based GUI application for managing and interacting with Ollama models.")
        info.SetCopyright("(C) 2025")
        info.AddDeveloper("LlamaLot Team")
        
        wx.adv.AboutBox(info, self)
    
    def on_refresh(self, event: wx.CommandEvent) -> None:
        """Handle refresh menu item."""
        logger.info("Refresh requested")
        self._load_models_async()
        self._load_conversations_async()
    
    def on_new_conversation(self, event: wx.CommandEvent) -> None:
        """Handle new conversation."""
        if not self.current_model:
            wx.MessageBox("Please select a model first", "No Model Selected", wx.OK | wx.ICON_WARNING)
            return
        
        # Create new conversation
        conv_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_conversation = ChatConversation(
            conversation_id=conv_id,
            title=f"Chat with {self.current_model.name}",
            model_name=self.current_model.name
        )
        
        # Save to database
        self.db_manager.save_conversation(self.current_conversation)
        
        # Clear chat display
        self.chat_display.Clear()
        
        # Refresh conversations list
        self._load_conversations_async()
        
        logger.info(f"Created new conversation: {conv_id}")
    
    def on_clear_chat(self, event: wx.CommandEvent) -> None:
        """Handle clear chat button."""
        self.chat_display.Clear()
    
    def on_send_message(self, event: wx.CommandEvent) -> None:
        """Handle send message button."""
        message_text = self.chat_input.GetValue().strip()
        if not message_text:
            return
        
        if not self.current_model:
            wx.MessageBox("Please select a model first", "No Model Selected", wx.OK | wx.ICON_WARNING)
            return
        
        if not self.current_conversation:
            self.on_new_conversation(None)
        
        # Clear input
        self.chat_input.Clear()
        
        # Add user message to display
        self._add_message_to_display("You", message_text)
        
        # Send message to model (async)
        wx.CallAfter(self._send_message_async, message_text)
    
    def on_chat_input_enter(self, event: wx.CommandEvent) -> None:
        """Handle Enter key in chat input."""
        if wx.GetKeyState(wx.WXK_CONTROL):
            self.on_send_message(event)
        else:
            event.Skip()  # Allow normal Enter behavior (new line)
    
    def on_model_selected(self, event: wx.ListEvent) -> None:
        """Handle model selection."""
        selection = event.GetIndex()
        if 0 <= selection < len(self.models):
            self.current_model = self.models[selection]
            
            # Update status bar
            self.status_bar.SetStatusText(f"Selected: {self.current_model.name}", 1)
            
            # Update chat header
            self.current_model_label.SetLabel(f"Chat with {self.current_model.name}")
            
            # Update model info
            info_text = f"Size: {self._format_size(self.current_model.size)}\n"
            info_text += f"Family: {self.current_model.details.family}\n"
            info_text += f"Modified: {self.current_model.modified_at.strftime('%Y-%m-%d %H:%M')}"
            self.model_info.SetLabel(info_text)
            
            logger.info(f"Selected model: {self.current_model.name}")
    
    def on_conversation_selected(self, event: wx.ListEvent) -> None:
        """Handle conversation selection."""
        selection = event.GetIndex()
        if 0 <= selection < len(self.conversations):
            self.current_conversation = self.conversations[selection]
            
            # Load conversation messages
            self._load_conversation_messages()
            
            # Update current model if different
            model = self.cache_manager.get_cached_model(self.current_conversation.model_name)
            if model:
                self.current_model = model
                self.current_model_label.SetLabel(f"Chat with {self.current_model.name}")
                self.status_bar.SetStatusText(f"Selected: {self.current_model.name}", 1)
            
            logger.info(f"Selected conversation: {self.current_conversation.title}")
    
    def _add_message_to_display(self, sender: str, message: str) -> None:
        """Add a message to the chat display."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {sender}: {message}\n\n"
        
        self.chat_display.AppendText(formatted_message)
        self.chat_display.SetInsertionPointEnd()
    
    def _send_message_async(self, message: str) -> None:
        """Send message to model asynchronously."""
        try:
            self.status_bar.SetStatusText("Sending message...", 0)
            
            # Create user message
            user_message = ChatMessage(
                role="user",
                content=message,
                timestamp=datetime.now()
            )
            
            # Save user message
            if self.current_conversation:
                self.db_manager.save_message(self.current_conversation.conversation_id, user_message)
            
            # Send to model
            response = self.ollama_client.chat_sync(
                model=self.current_model.name,
                messages=[user_message],
                stream=False
            )
            
            # Add response to display
            if response and response.content:
                self._add_message_to_display(self.current_model.name, response.content)
                
                # Save assistant message
                if self.current_conversation:
                    self.db_manager.save_message(self.current_conversation.conversation_id, response)
            
            self.status_bar.SetStatusText("Ready", 0)
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self.status_bar.SetStatusText("Error sending message", 0)
            self._add_message_to_display("Error", f"Failed to send message: {str(e)}")
    
    def _load_conversation_messages(self) -> None:
        """Load messages for the current conversation."""
        if not self.current_conversation:
            return
        
        try:
            messages = self.db_manager.get_conversation_messages(self.current_conversation.conversation_id)
            
            # Clear display
            self.chat_display.Clear()
            
            # Add messages
            for message in messages:
                sender = "You" if message.role == "user" else self.current_conversation.model_name
                # Format timestamp
                timestamp = message.timestamp.strftime("%H:%M:%S")
                formatted_message = f"[{timestamp}] {sender}: {message.content}\n\n"
                self.chat_display.AppendText(formatted_message)
            
            self.chat_display.SetInsertionPointEnd()
            
        except Exception as e:
            logger.error(f"Failed to load conversation messages: {e}")
            wx.MessageBox(
                f"Failed to load conversation messages:\n{str(e)}", 
                "Error", 
                wx.OK | wx.ICON_ERROR
            )
    
    def on_close(self, event: wx.CloseEvent) -> None:
        """Handle window close event."""
        logger.info("Main window closing")
        
        # Close backend connections
        try:
            if hasattr(self, 'db_manager'):
                self.db_manager.close()
        except Exception as e:
            logger.error(f"Error closing database: {e}")
        
        event.Skip()  # Allow the window to close
