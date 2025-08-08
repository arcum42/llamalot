"""
Enhanced main window for LlamaLot application.

Contains the enhanced GUI interface for managing Ollama models with
real backend integration.
"""

import wx
import wx.adv
import logging
import threading
import uuid
from typing import Optional, List
from datetime import datetime
from pathlib import Path

from llamalot.utils.logging_config import get_logger
from llamalot.backend.ollama_client import OllamaClient
from llamalot.backend.cache import CacheManager
from llamalot.backend.database import DatabaseManager
from llamalot.models import OllamaModel, ApplicationConfig, MessageRole
from llamalot.models.chat import ChatConversation, ChatMessage, ChatImage, MessageRole
from llamalot.gui.dialogs.image_viewer_dialog import ImageViewerDialog
from llamalot.gui.dialogs.model_pull_progress_dialog import ModelPullProgressDialog
from llamalot.gui.dialogs.settings_dialog import SettingsDialog
from llamalot.gui.dialogs.create_model_dialog import CreateModelDialog
from llamalot.gui.components.image_attachment_panel import ImageAttachmentPanel

logger = get_logger(__name__)


class EnhancedMainWindow(wx.Frame):
    """Enhanced main application window with real backend integration."""
    
    def __init__(self):
        """Initialize the enhanced main window."""
        # Initialize backend first to get config
        logger.info("Initializing enhanced main window")
        self._init_backend()
        
        # Use configuration for window size
        initial_size = wx.Size(
            self.config.ui_preferences.window_width,
            self.config.ui_preferences.window_height
        )
        
        super().__init__(
            parent=None,
            title="LlamaLot - Enhanced Ollama Model Manager",
            size=initial_size
        )
        
        # Set minimum size
        self.SetMinSize(wx.Size(1000, 700))
        
        # Apply window state from config
        if self.config.ui_preferences.window_maximized:
            self.Maximize()
        else:
            # Center the window
            self.Center()
        
        # Continue with initialization
        self._init_ui_and_data()
    
    def _init_ui_and_data(self) -> None:
        """Initialize UI components and load data."""
        # Initialize application state
        # Initialize model list
        self.models: List[OllamaModel] = []
        self.current_model: Optional[OllamaModel] = None
        
        # Sorting state
        self.sort_column: int = 1  # Default sort by Name column
        self.sort_ascending: bool = True
        self.current_conversation: Optional[ChatConversation] = None
        self._modelfile_loaded = False  # Track if modelfile has been loaded for current model
        
        # Chat history state
        self.selected_conversation_id: Optional[str] = None
        self.conversation_ids: List[str] = []  # Store conversation IDs for lookup
        
        # Create the main layout
        self._create_main_layout()
        
        # Create menu bar
        self._create_menu_bar()
        
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
            db_path = Path(self.config.database_file or "llamalot.db")
            self.db_manager = DatabaseManager(db_path)
            
            # Initialize Ollama client with config
            self.ollama_client = OllamaClient(self.config.ollama_server)
            
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
    
    def _create_main_layout(self) -> None:
        """Create the main layout with notebook tabs."""
        # Create main panel
        self.main_panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Create notebook for tabs
        self.notebook = wx.Notebook(self.main_panel)
        
        # Create tabs
        self._create_chat_tab()
        self._create_batch_tab()
        
        main_sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 5)
        self.main_panel.SetSizer(main_sizer)
        
        # Create status bar
        self.status_bar = self.CreateStatusBar(2)
        self.status_bar.SetStatusWidths([-1, 150])
        self.status_bar.SetStatusText("Ready", 0)
        self.status_bar.SetStatusText("No model selected", 1)
        
    def _create_menu_bar(self) -> None:
        """Create the menu bar."""
        menubar = wx.MenuBar()
        
        # File menu
        file_menu = wx.Menu()
        
        # Settings menu item
        settings_item = file_menu.Append(wx.ID_PREFERENCES, "&Settings...\tCtrl+,", "Open application settings")
        
        file_menu.AppendSeparator()
        
        # Exit menu item
        exit_item = file_menu.Append(wx.ID_EXIT, "E&xit\tCtrl+Q", "Exit the application")
        
        # Tools menu
        tools_menu = wx.Menu()
        
        # Refresh models
        refresh_item = tools_menu.Append(wx.ID_REFRESH, "&Refresh Models\tF5", "Refresh the model list")
        
        # Pull model
        pull_item = tools_menu.Append(wx.ID_ANY, "&Pull Model...", "Pull a new model from registry")
        
        # Help menu
        help_menu = wx.Menu()
        about_item = help_menu.Append(wx.ID_ABOUT, "&About", "About LlamaLot")
        
        # Add menus to menubar
        menubar.Append(file_menu, "&File")
        menubar.Append(tools_menu, "&Tools")
        menubar.Append(help_menu, "&Help")
        
        self.SetMenuBar(menubar)
        
        # Bind menu events
        self.Bind(wx.EVT_MENU, self._on_settings, settings_item)
        self.Bind(wx.EVT_MENU, self._on_exit, exit_item)
        self.Bind(wx.EVT_MENU, self._on_refresh_models, refresh_item)
        self.Bind(wx.EVT_MENU, self._on_about, about_item)
    
        
    def _create_chat_tab(self) -> None:
        """Create the main chat tab with existing functionality."""
        # Create chat panel (existing functionality)
        self.chat_panel = wx.Panel(self.notebook)
        
        # Create main splitter (horizontal - left/right) in chat tab
        self.main_splitter = wx.SplitterWindow(
            self.chat_panel, 
            style=wx.SP_3D | wx.SP_LIVE_UPDATE
        )
        self.main_splitter.SetMinimumPaneSize(250)
        
        # Create left panel (models)
        self.left_panel = wx.Panel(self.main_splitter)
        self._create_left_panel()
        
        # Create right panel (model details and basic chat)
        self.right_panel = wx.Panel(self.main_splitter)
        self._create_right_panel()
        
        # Split the main window - larger left panel to show all model columns
        self.main_splitter.SplitVertically(self.left_panel, self.right_panel, 600)
        
        # Chat tab sizer
        chat_sizer = wx.BoxSizer(wx.VERTICAL)
        chat_sizer.Add(self.main_splitter, 1, wx.EXPAND)
        self.chat_panel.SetSizer(chat_sizer)
        
        # Add tab to notebook
        self.notebook.AddPage(self.chat_panel, "💬 Chat", True)
        
    def _create_batch_tab(self) -> None:
        """Create the batch processing tab."""
        from llamalot.gui.components.batch_processing_panel import BatchProcessingPanel
        
        # Create batch processing panel
        self.batch_panel = BatchProcessingPanel(
            self.notebook,
            self.ollama_client,
            self.cache_manager,
            on_status_update=self._on_batch_status_update
        )
        
        # Add tab to notebook
        self.notebook.AddPage(self.batch_panel, "🔄 Batch Processing", False)
        
        # Create chat history tab
        self.create_chat_history_tab()
        
    def create_chat_history_tab(self) -> None:
        """Create the chat history tab with conversation list and viewer."""
        # Create the history panel
        self.history_panel = wx.Panel(self.notebook)
        
        # Main splitter for conversation list and detail view
        splitter = wx.SplitterWindow(self.history_panel, style=wx.SP_3D | wx.SP_LIVE_UPDATE)
        
        # Left panel: Conversation list
        list_panel = wx.Panel(splitter)
        list_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Header with refresh button
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        history_label = wx.StaticText(list_panel, label="Chat History")
        history_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        
        self.refresh_history_btn = wx.Button(list_panel, label="Refresh", size=wx.Size(80, 25))
        self.refresh_history_btn.SetToolTip("Refresh conversation list")
        
        header_sizer.Add(history_label, 1, wx.ALIGN_CENTER_VERTICAL)
        header_sizer.Add(self.refresh_history_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        
        # Conversation list
        self.conversation_list = wx.ListCtrl(
            list_panel,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES
        )
        
        # Setup conversation list columns
        self.conversation_list.AppendColumn("Title", width=200)
        self.conversation_list.AppendColumn("Model", width=120)
        self.conversation_list.AppendColumn("Messages", width=80)
        self.conversation_list.AppendColumn("Created", width=150)
        
        # Delete button
        self.delete_conversation_btn = wx.Button(list_panel, label="Delete")
        self.delete_conversation_btn.SetToolTip("Delete selected conversation")
        self.delete_conversation_btn.Enable(False)
        
        list_sizer.Add(header_sizer, 0, wx.EXPAND | wx.ALL, 5)
        list_sizer.Add(self.conversation_list, 1, wx.EXPAND | wx.ALL, 5)
        list_sizer.Add(self.delete_conversation_btn, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        list_panel.SetSizer(list_sizer)
        
        # Right panel: Conversation viewer
        viewer_panel = wx.Panel(splitter)
        viewer_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Conversation display
        self.conversation_display = wx.TextCtrl(
            viewer_panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2
        )
        self.conversation_display.SetFont(wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        
        viewer_sizer.Add(self.conversation_display, 1, wx.EXPAND | wx.ALL, 5)
        viewer_panel.SetSizer(viewer_sizer)
        
        # Setup splitter
        splitter.SplitVertically(list_panel, viewer_panel)
        splitter.SetMinimumPaneSize(200)
        splitter.SetSashPosition(400)
        
        # Main panel layout
        history_sizer = wx.BoxSizer(wx.VERTICAL)
        history_sizer.Add(splitter, 1, wx.EXPAND)
        self.history_panel.SetSizer(history_sizer)
        
        # Add tab to notebook
        self.notebook.AddPage(self.history_panel, "📚 History", False)
        
        # Bind events
        self.refresh_history_btn.Bind(wx.EVT_BUTTON, self.on_refresh_history)
        self.conversation_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_conversation_selected)
        self.conversation_list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.on_conversation_deselected)
        self.delete_conversation_btn.Bind(wx.EVT_BUTTON, self.on_delete_conversation)
        
        # Load initial conversation list
        self.refresh_conversation_list()
        
    def _on_batch_status_update(self, message: str) -> None:
        """Handle status updates from batch processing."""
        if hasattr(self, 'status_bar'):
            self.status_bar.SetStatusText(f"Batch: {message}", 1)
    
    def _create_left_panel(self) -> None:
        """Create the left panel with model list."""
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Model list header
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        model_label = wx.StaticText(self.left_panel, label="Available Models")
        model_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        
        # Refresh button
        self.refresh_btn = wx.Button(self.left_panel, label="Refresh", size=wx.Size(80, 25))
        self.refresh_btn.SetToolTip("Refresh model list from Ollama")
        
        header_sizer.Add(model_label, 1, wx.ALIGN_CENTER_VERTICAL)
        header_sizer.Add(self.refresh_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        
        # Model list control
        self.model_list = wx.ListCtrl(
            self.left_panel,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES
        )
        
        # Add columns - Running column first for visibility
        self.model_list.AppendColumn("Running", width=60)
        self.model_list.AppendColumn("Name", width=200)
        self.model_list.AppendColumn("Size", width=80)
        self.model_list.AppendColumn("Modified", width=100)
        self.model_list.AppendColumn("Capabilities", width=120)
        
        # Add to sizer
        sizer.Add(header_sizer, 0, wx.EXPAND | wx.ALL, 10)
        sizer.Add(self.model_list, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
        self.left_panel.SetSizer(sizer)
    
    def _create_right_panel(self) -> None:
        """Create the right panel with model management, chat section, and model information."""
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Model Management section
        mgmt_label = wx.StaticText(self.right_panel, label="Model Management")
        mgmt_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        
        # Model actions buttons
        action_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.pull_btn = wx.Button(self.right_panel, label="Pull Model", size=wx.Size(80, 25))
        self.create_btn = wx.Button(self.right_panel, label="Create Model", size=wx.Size(100, 25))
        self.delete_btn = wx.Button(self.right_panel, label="Delete", size=wx.Size(80, 25))
        
        # Initially disable action buttons until a model is selected
        self.delete_btn.Enable(False)
        
        action_sizer.Add(self.pull_btn, 0, wx.RIGHT, 5)
        action_sizer.Add(self.create_btn, 0, wx.RIGHT, 5)
        action_sizer.Add(self.delete_btn, 0)
        
        # Quick Chat section (moved up and given more space)
        chat_label = wx.StaticText(self.right_panel, label="Quick Chat")
        chat_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        
        # Chat output (larger now)
        self.chat_output = wx.TextCtrl(
            self.right_panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY,
            size=wx.Size(-1, 200)  # Increased from 120 to 200
        )
        
        # Replace the old image attachment section with the new component
        self.image_attachment_panel = ImageAttachmentPanel(
            self.right_panel,
            on_images_changed=self._on_images_changed
        )
        # Panel starts hidden - will be shown when a vision model is selected
        
        # Chat input
        input_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.chat_input = wx.TextCtrl(
            self.right_panel,
            style=wx.TE_PROCESS_ENTER,
            size=wx.Size(-1, 25)
        )
        self.send_btn = wx.Button(self.right_panel, label="Send", size=wx.Size(60, 25))
        self.new_chat_btn = wx.Button(self.right_panel, label="New Chat", size=wx.Size(80, 25))
        self.new_chat_btn.SetToolTip("Start a new conversation with the current model")
        
        input_sizer.Add(self.chat_input, 1, wx.EXPAND | wx.RIGHT, 5)
        input_sizer.Add(self.new_chat_btn, 0, wx.RIGHT, 5)
        input_sizer.Add(self.send_btn, 0)
        
        # Model details section with tabs (moved to bottom)
        info_label = wx.StaticText(self.right_panel, label="Model Information")
        info_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        
        self.details_notebook = wx.Notebook(self.right_panel)
        
        # Overview tab
        self.overview_panel = wx.Panel(self.details_notebook)
        self.overview_text = wx.TextCtrl(
            self.overview_panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY,
            size=wx.Size(-1, 120)  # Reduced from 150 to 120
        )
        self.overview_text.SetValue("Select a model to view details...")
        overview_sizer = wx.BoxSizer(wx.VERTICAL)
        overview_sizer.Add(self.overview_text, 1, wx.EXPAND | wx.ALL, 5)
        self.overview_panel.SetSizer(overview_sizer)
        
        # Capabilities tab
        self.capabilities_panel = wx.Panel(self.details_notebook)
        self.capabilities_text = wx.TextCtrl(
            self.capabilities_panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY,
            size=wx.Size(-1, 120)  # Reduced from 150 to 120
        )
        capabilities_sizer = wx.BoxSizer(wx.VERTICAL)
        capabilities_sizer.Add(self.capabilities_text, 1, wx.EXPAND | wx.ALL, 5)
        self.capabilities_panel.SetSizer(capabilities_sizer)
        
        # Modelfile tab
        self.modelfile_panel = wx.Panel(self.details_notebook)
        self.modelfile_text = wx.TextCtrl(
            self.modelfile_panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY,
            size=wx.Size(-1, 120)  # Reduced from 150 to 120
        )
        modelfile_sizer = wx.BoxSizer(wx.VERTICAL)
        modelfile_sizer.Add(self.modelfile_text, 1, wx.EXPAND | wx.ALL, 5)
        self.modelfile_panel.SetSizer(modelfile_sizer)
        
        # Add tabs to notebook
        self.details_notebook.AddPage(self.overview_panel, "Overview")
        self.details_notebook.AddPage(self.capabilities_panel, "Capabilities")
        self.details_notebook.AddPage(self.modelfile_panel, "Modelfile")
        
        # Add to main sizer with new layout order
        sizer.Add(mgmt_label, 0, wx.ALL, 10)
        sizer.Add(action_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        sizer.Add(chat_label, 0, wx.ALL, 10)
        sizer.Add(self.chat_output, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)  # Changed proportion to 1 for more space
        sizer.Add(self.image_attachment_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)  # New image attachment component
        sizer.Add(input_sizer, 0, wx.EXPAND | wx.ALL, 10)
        sizer.Add(info_label, 0, wx.ALL, 10)
        sizer.Add(self.details_notebook, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)  # Changed proportion to 0
        
        self.right_panel.SetSizer(sizer)
        
    
    def _bind_events(self) -> None:
        """Bind event handlers."""
        # Button events
        self.Bind(wx.EVT_BUTTON, self.on_refresh, self.refresh_btn)
        self.Bind(wx.EVT_BUTTON, self.on_pull_model, self.pull_btn)
        self.Bind(wx.EVT_BUTTON, self.on_create_model, self.create_btn)
        self.Bind(wx.EVT_BUTTON, self.on_delete_model, self.delete_btn)
        self.Bind(wx.EVT_BUTTON, self.on_send_message, self.send_btn)
        self.Bind(wx.EVT_BUTTON, self.on_new_chat, self.new_chat_btn)
        
        # List events
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_model_selected, self.model_list)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.on_column_click, self.model_list)
        
        # Notebook events
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_tab_changed, self.details_notebook)
        
        # Text events
        self.Bind(wx.EVT_TEXT_ENTER, self.on_chat_input_enter, self.chat_input)
        
        # Window events
        self.Bind(wx.EVT_CLOSE, self.on_close)
        
        # Apply initial settings
        self._apply_initial_settings()
    
    def _apply_initial_settings(self) -> None:
        """Apply settings when the window is first created."""
        try:
            # Apply font settings
            self._apply_chat_font_settings()
            
            logger.debug("Applied initial settings")
            
        except Exception as e:
            logger.error(f"Error applying initial settings: {e}")
    
    def _load_initial_data(self) -> None:
        """Load initial data on startup."""
        wx.CallAfter(self._load_models_async)
    
    def _load_models_async(self) -> None:
        """Load models asynchronously."""
        try:
            self.status_bar.SetStatusText("Loading models...", 0)
            
            # Get models from cache (smart caching - only refresh if needed)
            self.models = self.cache_manager.get_models(force_refresh=False)
            
            # Apply initial sorting
            self._sort_models()
            
            # Update model list
            self._update_model_list()
            
            # Auto-select default model if configured
            if (self.config.ui_preferences.auto_select_default_model and 
                self.config.ui_preferences.default_model and 
                not self.current_model):  # Only auto-select if no model is currently selected
                self._select_default_model()
            
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
    
    def _update_model_list(self) -> None:
        """Update the model list display."""
        self.model_list.DeleteAllItems()
        
        # Get running models
        running_models = []
        try:
            running_models = self.ollama_client.get_running_models()
        except Exception as e:
            logger.warning(f"Could not get running models: {e}")
        
        for i, model in enumerate(self.models):
            # Check if running
            running_str = "●" if model.name in running_models else ""
            
            # Format size
            size_str = self._format_size(model.size)
            
            # Format date
            date_str = model.modified_at.strftime("%m/%d/%y") if model.modified_at else "Unknown"
            
            # Format capabilities
            capabilities_str = ", ".join(model.capabilities) if model.capabilities else "text"
            
            # Add to list - Running column first (0), then Name (1), Size (2), Modified (3), Capabilities (4)
            index = self.model_list.InsertItem(i, running_str)  # Running column first
            self.model_list.SetItem(index, 1, model.name)       # Name
            self.model_list.SetItem(index, 2, size_str)         # Size
            self.model_list.SetItem(index, 3, date_str)         # Modified
            self.model_list.SetItem(index, 4, capabilities_str) # Capabilities
        
        # Update column headers with sort indicators
        self._update_column_headers()
    
    def _format_size(self, size_bytes: int) -> str:
        """Format size in bytes to human readable string."""
        size = float(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f}{unit}"
            size /= 1024.0
        return f"{size:.1f}PB"
    
    def _select_model_by_name_after_delay(self, model_name: str) -> None:
        """Select a model by name after a short delay to allow list refresh."""
        def select_after_delay():
            """Wait a bit then try to select the model."""
            import time
            time.sleep(0.5)  # Give refresh time to complete
            wx.CallAfter(self._select_model_by_name, model_name)
        
        # Start delay in background thread
        delay_thread = threading.Thread(target=select_after_delay, daemon=True)
        delay_thread.start()
    
    def _select_model_by_name(self, model_name: str) -> None:
        """Select a model in the list by name."""
        try:
            # Find the model in the current list
            for i, model in enumerate(self.models):
                if model.name == model_name:
                    # Select the item in the list
                    self.model_list.Select(i)
                    self.model_list.EnsureVisible(i)
                    
                    # Trigger the selection event manually to update UI
                    self.current_model = model
                    self.delete_btn.Enable(True)
                    self._update_model_details()
                    self._update_image_panel_visibility()
                    self._start_new_conversation()
                    
                    logger.info(f"Auto-selected created model: {model_name}")
                    break
            else:
                logger.warning(f"Could not find created model in list: {model_name}")
        except Exception as e:
            logger.error(f"Error selecting model {model_name}: {e}")

    def _on_images_changed(self, images: List[ChatImage]) -> None:
        """Callback when images are updated in the attachment panel."""
        # Store the images for use in chat messages
        self.attached_images = images
        logger.info(f"Images updated: {len(images)} images attached")
    
    # Event handlers
    def on_refresh(self, event: wx.CommandEvent) -> None:
        """Handle refresh button - force refresh from server."""
        logger.info("Manual refresh requested - forcing server refresh")
        
        # Disable refresh button to prevent multiple simultaneous refreshes
        self.refresh_btn.Enable(False)
        self.status_bar.SetStatusText("Refreshing models from server...", 0)
        
        def refresh_worker():
            """Worker thread to perform the refresh."""
            try:
                # Update status periodically
                wx.CallAfter(self.status_bar.SetStatusText, "Fetching model list...", 0)
                
                # Force refresh from server
                models = self.cache_manager.get_models(force_refresh=True)
                
                # Update GUI on main thread
                wx.CallAfter(self._refresh_complete, models, None)
                
            except Exception as e:
                # Update GUI on main thread with error
                wx.CallAfter(self._refresh_complete, None, e)
        
        # Start refresh in background thread
        refresh_thread = threading.Thread(target=refresh_worker, daemon=True)
        refresh_thread.start()
    
    def _refresh_complete(self, models: Optional[List[OllamaModel]], error: Optional[Exception]) -> None:
        """Handle completion of refresh operation (called on main thread)."""
        # Re-enable refresh button
        self.refresh_btn.Enable(True)
        
        if error:
            logger.error(f"Failed to refresh models: {error}")
            self.status_bar.SetStatusText("Error refreshing models", 0)
            wx.MessageBox(
                f"Failed to refresh models:\n{str(error)}", 
                "Refresh Error", 
                wx.OK | wx.ICON_ERROR
            )
        elif models is not None:
            # Update model list
            self.models = models
            
            # Apply current sorting
            self._sort_models()
            
            self._update_model_list()
            
            self.status_bar.SetStatusText("Ready", 0)
            self.status_bar.SetStatusText(f"{len(self.models)} models", 1)
            
            logger.info("Manual refresh completed successfully")
    
    def on_model_selected(self, event: wx.ListEvent) -> None:
        """Handle model selection."""
        selection = self.model_list.GetFirstSelected()
        if selection >= 0 and selection < len(self.models):
            self.current_model = self.models[selection]
            
            # Enable action buttons
            self.delete_btn.Enable(True)
            
            # Update status bar (now we know current_model is not None)
            assert self.current_model is not None
            self.status_bar.SetStatusText(f"Selected: {self.current_model.name}", 1)
            
            # Update model details in the notebook tabs
            self._update_model_details()
            
            # Show/hide image panel based on vision capabilities
            self._update_image_panel_visibility()
            
            # Save current conversation before starting a new one
            self.save_current_conversation()
            
            # Initialize a new conversation for this model
            self._start_new_conversation()
            
            # Clear chat and show ready message
            self.chat_output.Clear()
            self.chat_output.AppendText(f"Ready to chat with {self.current_model.name}\n")
            self.chat_output.AppendText("Type a message and press Enter or click Send.\n")
            
            # Show image hint for vision models
            if "vision" in self.current_model.capabilities:
                self.chat_output.AppendText("📷 This model supports vision! You can attach images to your messages.\n")
            self.chat_output.AppendText("\n")
            
            logger.info(f"Selected model: {self.current_model.name}")
    
    def on_column_click(self, event: wx.ListEvent) -> None:
        """Handle column header click for sorting."""
        column = event.GetColumn()
        
        # If clicking the same column, toggle sort order
        if self.sort_column == column:
            self.sort_ascending = not self.sort_ascending
        else:
            # New column, default to ascending
            self.sort_column = column
            self.sort_ascending = True
        
        # Sort models and update display
        self._sort_models()
        self._update_model_list()
        
        # Update column headers with sort indicators
        self._update_column_headers()
        
        # Re-select the previously selected model if it exists
        if self.current_model:
            self._reselect_current_model()
        
        logger.info(f"Sorted by column {column} ({'ascending' if self.sort_ascending else 'descending'})")
    
    def _sort_models(self) -> None:
        """Sort models based on current sort column and order."""
        if not self.models:
            return
        
        # Define sort functions for each column
        def get_sort_key(model: OllamaModel):
            if self.sort_column == 0:  # Running
                # Get running models for sorting
                try:
                    running_models = self.ollama_client.get_running_models()
                    return model.name in running_models
                except:
                    return False
            elif self.sort_column == 1:  # Name
                return model.name.lower()
            elif self.sort_column == 2:  # Size
                return model.size
            elif self.sort_column == 3:  # Modified
                if model.modified_at:
                    return model.modified_at
                else:
                    # Use epoch time for models without modified_at
                    return datetime.fromtimestamp(0)
            elif self.sort_column == 4:  # Capabilities
                return ", ".join(sorted(model.capabilities)) if model.capabilities else ""
            else:
                return model.name.lower()  # Fallback to name
        
        self.models.sort(key=get_sort_key, reverse=not self.sort_ascending)
    
    def _update_column_headers(self) -> None:
        """Update column headers with sort indicators."""
        # Column names without indicators
        base_headers = ["Running", "Name", "Size", "Modified", "Capabilities"]
        
        for i, header in enumerate(base_headers):
            if i == self.sort_column:
                # Add sort indicator
                indicator = " ↑" if self.sort_ascending else " ↓"
                self.model_list.SetColumn(i, wx.ListItem())
                col_info = self.model_list.GetColumn(i)
                col_info.SetText(header + indicator)
                self.model_list.SetColumn(i, col_info)
            else:
                # Remove indicator
                self.model_list.SetColumn(i, wx.ListItem())
                col_info = self.model_list.GetColumn(i)
                col_info.SetText(header)
                self.model_list.SetColumn(i, col_info)
    
    def _reselect_current_model(self) -> None:
        """Re-select the current model after sorting."""
        if not self.current_model:
            return
        
        # Find the new index of the current model
        for i, model in enumerate(self.models):
            if model.name == self.current_model.name:
                self.model_list.Select(i)
                self.model_list.EnsureVisible(i)
                break
    
    def _update_model_details(self) -> None:
        """Update the model details tabs with comprehensive information."""
        if not self.current_model:
            return
        
        # Reset modelfile loaded flag for new model
        self._modelfile_loaded = False
            
        # Update Overview tab
        overview_info = f"Model: {self.current_model.name}\n"
        overview_info += f"Size: {self._format_size(self.current_model.size)}\n"
        overview_info += f"Modified: {self.current_model.modified_at.strftime('%Y-%m-%d %H:%M') if self.current_model.modified_at else 'Unknown'}\n"
        overview_info += f"Digest: {self.current_model.digest[:16] if self.current_model.digest else 'Unknown'}...\n\n"
        
        # Model section (similar to ollama show output)
        overview_info += "Model:\n"
        overview_info += f"  architecture        {self.current_model.details.family or 'Unknown'}\n"
        if self.current_model.details.parameter_size:
            overview_info += f"  parameters          {self.current_model.details.parameter_size}\n"
        elif self.current_model.model_info and self.current_model.model_info.parameter_count:
            # Format parameter count as B (billions) or M (millions)
            param_count = self.current_model.model_info.parameter_count
            if param_count >= 1_000_000_000:
                param_str = f"{param_count / 1_000_000_000:.1f}B"
            elif param_count >= 1_000_000:
                param_str = f"{param_count / 1_000_000:.1f}M"
            else:
                param_str = f"{param_count:,}"
            overview_info += f"  parameters          {param_str}\n"
        
        if self.current_model.model_info and self.current_model.model_info.context_length:
            overview_info += f"  context length      {self.current_model.model_info.context_length:,}\n"
        if self.current_model.model_info and self.current_model.model_info.embedding_length:
            overview_info += f"  embedding length    {self.current_model.model_info.embedding_length:,}\n"
        if self.current_model.details.quantization_level:
            overview_info += f"  quantization        {self.current_model.details.quantization_level}\n"
        
        # Additional technical details section
        if self.current_model.model_info:
            has_technical_info = any([
                self.current_model.model_info.attention_head_count,
                self.current_model.model_info.attention_head_count_kv,
                self.current_model.model_info.block_count,
                self.current_model.model_info.feed_forward_length,
                self.current_model.model_info.vocab_size
            ])
            
            if has_technical_info:
                overview_info += "\nTechnical Details:\n"
                if self.current_model.model_info.attention_head_count:
                    overview_info += f"  attention heads     {self.current_model.model_info.attention_head_count}\n"
                if self.current_model.model_info.attention_head_count_kv:
                    overview_info += f"  key-value heads     {self.current_model.model_info.attention_head_count_kv}\n"
                if self.current_model.model_info.block_count:
                    overview_info += f"  transformer blocks  {self.current_model.model_info.block_count}\n"
                if self.current_model.model_info.feed_forward_length:
                    overview_info += f"  feed forward size   {self.current_model.model_info.feed_forward_length:,}\n"
                if self.current_model.model_info.vocab_size:
                    overview_info += f"  vocabulary size     {self.current_model.model_info.vocab_size:,}\n"
        
        # File format information
        if self.current_model.details.format:
            overview_info += f"\nFile Format: {self.current_model.details.format.upper()}\n"
        
        self.overview_text.SetValue(overview_info)
        
        # Update Capabilities tab
        if hasattr(self.current_model, 'capabilities') and self.current_model.capabilities:
            capabilities_info = "Detected Capabilities:\n\n"
            for capability in self.current_model.capabilities:
                capabilities_info += f"• {capability.upper()}\n"
                
                # Add explanations
                if capability == "completion":
                    capabilities_info += "  - Text completion and generation\n"
                elif capability == "vision":
                    capabilities_info += "  - Image analysis and understanding\n"
                elif capability == "embedding":
                    capabilities_info += "  - Vector embeddings for RAG applications\n"
                elif capability == "tools":
                    capabilities_info += "  - Function calling and tool usage\n"
                capabilities_info += "\n"
        else:
            capabilities_info = "No specific capabilities detected.\nThis model likely supports text completion."
        
        self.capabilities_text.SetValue(capabilities_info)
        
        # Update Modelfile tab - clear previous content and mark as ready to load
        self.modelfile_text.SetValue("Select the Modelfile tab to load content...")
        
        # Mark that modelfile needs to be loaded
        self._modelfile_loaded = False
    
    def _update_image_panel_visibility(self) -> None:
        """Show or hide the image panel based on model capabilities."""
        if self.current_model and "vision" in self.current_model.capabilities:
            self.image_attachment_panel.show_panel(True)
        else:
            self.image_attachment_panel.show_panel(False)
            # Clear any attached images
            self.image_attachment_panel.clear_images()
        
        # Refresh layout
        self.right_panel.Layout()
        logger.info(f"Image panel visible: {self.image_attachment_panel.IsShown()}")
    
    def _start_new_conversation(self) -> None:
        """Start a new conversation with the current model."""
        if not self.current_model:
            return
            
        self.current_conversation = ChatConversation(
            conversation_id=str(uuid.uuid4()),
            title=f"Chat with {self.current_model.name}",
            model_name=self.current_model.name
        )
        # Initialize attached_images list
        self.attached_images = []
        logger.debug(f"Started new conversation with {self.current_model.name}")
    
    def on_send_message(self, event: wx.CommandEvent) -> None:
        """Handle send message button."""
        self._send_chat_message()
    
    def on_chat_input_enter(self, event: wx.CommandEvent) -> None:
        """Handle Enter key in chat input."""
        self._send_chat_message()
    
    def _send_chat_message(self) -> None:
        """Send chat message to the current model."""
        message_text = self.chat_input.GetValue().strip()
        if not message_text:
            return
        
        if not self.current_model:
            wx.MessageBox("Please select a model first", "No Model Selected", wx.OK | wx.ICON_WARNING)
            return
            
        if not self.current_conversation:
            self._start_new_conversation()
        
        # Get attached images from the component
        attached_images = self.image_attachment_panel.get_attached_images()
        
        # Clear input and disable controls
        self.chat_input.Clear()
        self.send_btn.Disable()
        self.chat_input.Disable()
        
        # Add user message to display (including image info)
        display_message = self._format_message_for_display(f"> {message_text}", "user", attached_images)
        self.chat_output.AppendText(display_message)
        self._auto_scroll_chat()
        
        # Show that we're processing
        self.status_bar.SetStatusText("Generating response...", 0)
        
        # Send message asynchronously
        wx.CallAfter(self._send_message_async, message_text, attached_images)
    
    def _send_message_async(self, message: str, attached_images: List[ChatImage]) -> None:
        """Send message to model asynchronously with streaming."""
        import threading
        
        # Start the assistant response in the UI
        wx.CallAfter(self._start_assistant_response)
        
        def send_in_thread():
            try:
                if not self.current_model or not self.current_conversation:
                    wx.CallAfter(self._handle_send_error, "No model or conversation available")
                    return
                
                # Create user message with attached images
                user_message = ChatMessage.create_user_message(message, images=attached_images)
                self.current_conversation.add_message(user_message)
                
                # Clear attached images after sending
                wx.CallAfter(self.image_attachment_panel.clear_images)
                
                # Send to model with streaming callback
                logger.debug(f"Sending message to {self.current_model.name} with streaming")
                
                # Use configuration settings for the chat
                stream_callback = self._stream_callback if self.config.chat_defaults.stream_responses else None
                
                response_message = self.ollama_client.chat(
                    model_name=self.current_model.name,
                    conversation=self.current_conversation,
                    stream_callback=stream_callback,
                    temperature=self.config.chat_defaults.temperature,
                    top_p=self.config.chat_defaults.top_p,
                    top_k=self.config.chat_defaults.top_k,
                    repeat_penalty=self.config.chat_defaults.repeat_penalty,
                    context_length=self.config.chat_defaults.context_length,
                    keep_alive=self.config.chat_defaults.keep_alive
                )
                
                # Add response to conversation
                self.current_conversation.add_message(response_message)
                
                # Auto-save the conversation after each exchange
                wx.CallAfter(self.save_current_conversation)
                
                # Finalize the response in UI
                wx.CallAfter(self._finalize_response)
                
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
                wx.CallAfter(self._handle_send_error, str(e))
        
        # Start thread
        thread = threading.Thread(target=send_in_thread, daemon=True)
        thread.start()
    
    def _start_assistant_response(self) -> None:
        """Start the assistant response in the UI."""
        assistant_start = self._format_message_for_display("🤖 Assistant:", "assistant")
        self.chat_output.AppendText(assistant_start)
        self._auto_scroll_chat()
        self.status_bar.SetStatusText("Generating response...", 0)
    
    def _stream_callback(self, chunk: str) -> None:
        """Handle streaming response chunks."""
        # Update UI from main thread
        wx.CallAfter(self._append_response_chunk, chunk)
    
    def _append_response_chunk(self, chunk: str) -> None:
        """Append a chunk of response to the chat display."""
        self.chat_output.AppendText(chunk)
        # Auto-scroll if enabled
        self._auto_scroll_chat()
    
    def _finalize_response(self) -> None:
        """Finalize the response and re-enable UI."""
        self.chat_output.AppendText(f"\n")
        self._auto_scroll_chat()
        self.status_bar.SetStatusText("Ready", 0)
        self.send_btn.Enable()
        self.chat_input.Enable()
        self.chat_input.SetFocus()
        
        # Refresh model list to update running status since we just chatted with a model
        self._refresh_model_running_status()
    
    def _handle_send_error(self, error: str) -> None:
        """Handle send error."""
        error_message = self._format_message_for_display(f"Error: {error}", "system")
        self.chat_output.AppendText(error_message)
        self._auto_scroll_chat()
        self.status_bar.SetStatusText("Error - Ready", 0)
        self.send_btn.Enable()
        self.chat_input.Enable()
        self.chat_input.SetFocus()
    
    def save_current_conversation(self) -> None:
        """Save the current conversation to the database if it has messages."""
        try:
            if self.current_conversation and len(self.current_conversation.messages) > 0:
                # Generate a better title if it's still the default
                if not self.current_conversation.title or self.current_conversation.title.startswith("Chat with"):
                    self.current_conversation.title = self._generate_conversation_title()
                
                # Save to database
                self.db_manager.save_conversation(self.current_conversation)
                logger.info(f"Saved conversation: {self.current_conversation.title}")
                
                # Refresh chat history if the tab is open
                wx.CallAfter(self.refresh_conversation_list)
                
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
    
    def _generate_conversation_title(self) -> str:
        """Generate a human-readable title for the conversation."""
        try:
            if not self.current_conversation or not self.current_conversation.messages:
                return f"Empty Chat - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            # Get the current date for the title
            date_str = datetime.now().strftime('%Y-%m-%d')
            
            # Find the first user message
            first_user_msg = next((msg for msg in self.current_conversation.messages if msg.role == MessageRole.USER), None)
            
            if not first_user_msg or not first_user_msg.content.strip():
                return f"Chat - {date_str}"
            
            # Clean and extract meaningful part of the first message
            content = first_user_msg.content.strip()
            
            # Remove common chat starters and get to the meat of the question
            content = self._clean_message_for_title(content)
            
            # If the conversation has multiple exchanges, try to get an AI summary
            if (len(self.current_conversation.messages) >= 4 and  # At least 2 exchanges
                self.config.ui_preferences.use_ai_generated_titles):  # AI titles enabled
                ai_title = self._generate_ai_summary_title(content, date_str)
                if ai_title:
                    return ai_title
            
            # Fallback to cleaned first message
            if len(content) > 40:
                content = content[:40].strip() + "..."
            
            return f"{content} - {date_str}"
            
        except Exception as e:
            logger.error(f"Error generating conversation title: {e}")
            return f"Chat - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    def _clean_message_for_title(self, content: str) -> str:
        """Clean a message to extract the meaningful part for a title."""
        # Remove common chat starters
        starters_to_remove = [
            "hi", "hello", "hey", "please", "can you", "could you", 
            "would you", "i need", "help me", "i want", "i'm looking for"
        ]
        
        # Split into words and process
        words = content.lower().split()
        
        # Remove common starters from the beginning
        while words and any(words[0].startswith(starter) for starter in starters_to_remove):
            words.pop(0)
        
        # Rejoin and capitalize appropriately
        if words:
            cleaned = ' '.join(words)
            # Capitalize first letter
            cleaned = cleaned[0].upper() + cleaned[1:] if len(cleaned) > 1 else cleaned.upper()
            return cleaned
        
        return content
    
    def _generate_ai_summary_title(self, first_message: str, date_str: str) -> Optional[str]:
        """Generate an AI-powered summary title for longer conversations."""
        try:
            if not self.current_model or not self.ollama_client or not self.current_conversation:
                return None
            
            # Get conversation context (first few and last few messages)
            messages = self.current_conversation.messages
            context_messages = []
            
            # Add first 2 messages
            context_messages.extend(messages[:2])
            
            # Add last 2 messages if conversation is long enough
            if len(messages) > 4:
                context_messages.extend(messages[-2:])
            
            # Build context string
            context = ""
            for msg in context_messages:
                role = "User" if msg.role == MessageRole.USER else "Assistant"
                content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
                context += f"{role}: {content}\n"
            
            # Create prompt for title generation
            title_prompt = f"""Based on this conversation, generate a short, descriptive title (3-6 words max) that captures the main topic or question. Do not include the date, model name, or chat-related words like "chat" or "conversation".

Conversation:
{context}

Title:"""
            
            # Use the current model to generate a title
            # Create a simple message for title generation
            from llamalot.models.chat import ChatMessage, ChatConversation
            
            # Create a temporary conversation for title generation
            temp_conversation = ChatConversation(
                conversation_id="temp_title",
                title="Temp",
                model_name=self.current_model.name
            )
            
            title_msg = ChatMessage(
                role=MessageRole.USER,
                content=title_prompt,
                timestamp=datetime.now()
            )
            temp_conversation.add_message(title_msg)
            
            # Get a quick response (no streaming, short)
            response = self.ollama_client.chat(
                model_name=self.current_model.name,
                messages=[title_msg],
                conversation=temp_conversation,
                stream=False,
                options={
                    'temperature': 0.3,  # Lower temperature for more focused titles
                    'num_predict': 20,   # Short response
                    'top_p': 0.9
                }
            )
            
            if response and hasattr(response, 'content') and response.content:
                # Clean up the AI response
                ai_title = response.content.strip().strip('"').strip("'")
                
                # Remove any remaining chat-related words
                ai_title = ai_title.replace("Chat about", "").replace("Discussion on", "").strip()
                
                # Limit length and add date
                if len(ai_title) > 50:
                    ai_title = ai_title[:50].strip() + "..."
                
                if ai_title and len(ai_title) > 3:  # Make sure we got something meaningful
                    return f"{ai_title} - {date_str}"
            
        except Exception as e:
            logger.debug(f"Could not generate AI title: {e}")
        
        return None
    
    def on_new_chat(self, event: wx.CommandEvent) -> None:
        """Handle new chat button click."""
        try:
            # Save current conversation if it exists and has messages
            self.save_current_conversation()
            
            # Clear the chat display
            self.chat_output.SetValue("")
            
            # Start a new conversation with the current model
            if self.current_model:
                self._start_new_conversation()
                logger.info(f"Started new chat with {self.current_model.name}")
                
                # Update status
                self.status_bar.SetStatusText(f"New chat started with {self.current_model.name}", 0)
            else:
                wx.MessageBox("Please select a model first.", "No Model Selected", wx.OK | wx.ICON_WARNING)
                
        except Exception as e:
            logger.error(f"Error starting new chat: {e}")
            wx.MessageBox(f"Error starting new chat: {e}", "Error", wx.OK | wx.ICON_ERROR)
    
    def _refresh_model_running_status(self) -> None:
        """Refresh only the running status of models without full reload."""
        try:
            # Get current running models
            running_models = self.ollama_client.get_running_models()
            
            # Update the Running column for each item in the list
            for i in range(self.model_list.GetItemCount()):
                # Get the model name from column 1 (Name column)
                model_name = self.model_list.GetItemText(i, 1)
                
                # Update the Running column (column 0)
                running_str = "●" if model_name in running_models else ""
                self.model_list.SetItem(i, 0, running_str)
                
            logger.info(f"Updated running status for {len(running_models)} running models")
            
        except Exception as e:
            logger.error(f"Error refreshing model running status: {e}")
    
    # Model management methods
    def on_pull_model(self, event: wx.CommandEvent) -> None:
        """Handle pull model button."""
        # Create input dialog with validation
        with wx.TextEntryDialog(self, 
                              "Enter model name to pull (e.g., 'phi3:latest'):\n\n" +
                              "Format: model:tag\n" +
                              "Examples: phi3:latest, llama3:8b, gemma:2b", 
                              "Pull Model") as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                model_name = dialog.GetValue().strip()
                if not model_name:
                    wx.MessageBox("Please enter a model name.", "Error", wx.OK | wx.ICON_ERROR)
                    return
                
                # Basic validation for model:tag format
                if ':' not in model_name:
                    result = wx.MessageBox(
                        f"Model name '{model_name}' doesn't include a tag.\n\n" +
                        "Would you like to add ':latest' automatically?",
                        "Add Tag?", wx.YES_NO | wx.ICON_QUESTION)
                    if result == wx.YES:
                        model_name += ":latest"
                    else:
                        return
                
                self._pull_model_with_progress(model_name)
    
    def _pull_model_with_progress(self, model_name: str) -> None:
        """Pull a model with progress dialog."""
        # Create progress dialog
        progress_dialog = ModelPullProgressDialog(self, model_name)
        
        # Variables to track pull result
        pull_successful = False
        error_message = ""
        
        def progress_callback(status: str, data: dict) -> None:
            """Callback to update progress dialog."""
            if not progress_dialog.is_cancelled():
                wx.CallAfter(progress_dialog.update_progress, status, data)
        
        def pull_worker():
            """Worker thread to perform the actual pull."""
            nonlocal pull_successful, error_message
            try:
                # Perform the pull with progress callback and cancellation checker
                pull_successful = self.ollama_client.pull_model(
                    model_name, 
                    progress_callback, 
                    cancellation_checker=lambda: progress_dialog.is_cancelled()
                )
                
                # Close dialog on success (if not cancelled)
                if pull_successful and not progress_dialog.is_cancelled():
                    wx.CallAfter(progress_dialog.EndModal, wx.ID_OK)
                elif progress_dialog.is_cancelled():
                    wx.CallAfter(progress_dialog.EndModal, wx.ID_CANCEL)
                    
            except Exception as e:
                error_message = str(e)
                logger.error(f"Error pulling model {model_name}: {e}")
                if not progress_dialog.is_cancelled():
                    wx.CallAfter(progress_dialog.EndModal, wx.ID_CANCEL)
        
        # Start pull in background thread
        pull_thread = threading.Thread(target=pull_worker, daemon=True)
        pull_thread.start()
        
        # Show progress dialog (blocking)
        result = progress_dialog.ShowModal()
        
        # Handle result
        if result == wx.ID_OK and pull_successful:
            wx.MessageBox(f"Successfully pulled model '{model_name}'!", 
                         "Pull Complete", wx.OK | wx.ICON_INFORMATION)
            # Refresh model list to show new model
            self._load_models_async()
        elif result == wx.ID_CANCEL and progress_dialog.is_cancelled():
            wx.MessageBox(f"Model pull cancelled for '{model_name}'.\n\nNote: Partial download data may remain on disk.", 
                         "Pull Cancelled", wx.OK | wx.ICON_INFORMATION)
        elif result == wx.ID_CANCEL and error_message:
            wx.MessageBox(f"Failed to pull model '{model_name}':\n\n{error_message}", 
                         "Pull Failed", wx.OK | wx.ICON_ERROR)
        else:
            wx.MessageBox(f"Model pull did not complete successfully for '{model_name}'.", 
                         "Pull Incomplete", wx.OK | wx.ICON_WARNING)
        
        progress_dialog.Destroy()

    def on_create_model(self, event: wx.CommandEvent) -> None:
        """Handle create model button."""
        # Get initial modelfile content from current model if selected
        initial_modelfile = ""
        if self.current_model:
            try:
                initial_modelfile = self.ollama_client.get_modelfile(self.current_model.name)
                logger.info(f"Retrieved modelfile for {self.current_model.name}")
            except Exception as e:
                logger.warning(f"Could not retrieve modelfile for {self.current_model.name}: {e}")
                # Continue with empty modelfile
        
        # Create and show the create model dialog
        with CreateModelDialog(self, self.ollama_client, initial_modelfile) as dialog:
            result = dialog.ShowModal()
            
            if result == wx.ID_OK:
                created_model_name = dialog.get_created_model_name()
                if created_model_name:
                    logger.info(f"Model created successfully: {created_model_name}")
                    
                    # Refresh model list to show new model
                    self._load_models_async()
                    
                    # Try to select the new model in the list after refresh
                    wx.CallAfter(self._select_model_by_name_after_delay, created_model_name)
                else:
                    logger.warning("Create model dialog reported success but no model name returned")

    def on_delete_model(self, event: wx.CommandEvent) -> None:
        """Handle delete model button."""
        if not self.current_model:
            return
        
        model_name = self.current_model.name
        
        # Check if confirmation is required
        if self.config.ui_preferences.confirm_model_deletion:
            # Enhanced confirmation dialog with more details
            with wx.MessageDialog(self, 
                                f"Are you sure you want to delete model '{model_name}'?\n\n"
                                f"This will permanently remove the model from your local storage.\n"
                                f"You will need to download it again if you want to use it later.\n\n"
                                f"Model size: {self.current_model.size / (1024*1024*1024):.1f} GB",
                                "Delete Model", 
                                wx.YES_NO | wx.ICON_QUESTION) as dialog:
                if dialog.ShowModal() == wx.ID_YES:
                    self._delete_model_with_feedback(model_name)
        else:
            # Delete directly without confirmation
            self._delete_model_with_feedback(model_name)
    
    def _delete_model_with_feedback(self, model_name: str) -> None:
        """Delete a model with user feedback."""
        def delete_worker():
            """Worker thread to perform the actual deletion."""
            try:
                # Perform the deletion
                success = self.ollama_client.delete_model(model_name)
                
                if success:
                    # Update GUI on main thread
                    wx.CallAfter(self._on_delete_success, model_name)
                else:
                    wx.CallAfter(self._on_delete_failure, model_name, "Unknown error occurred")
                    
            except Exception as e:
                logger.error(f"Error deleting model {model_name}: {e}")
                wx.CallAfter(self._on_delete_failure, model_name, str(e))
        
        # Show progress cursor
        wx.BeginBusyCursor()
        
        # Start deletion in background thread
        delete_thread = threading.Thread(target=delete_worker, daemon=True)
        delete_thread.start()
    
    def _on_delete_success(self, model_name: str) -> None:
        """Handle successful model deletion."""
        wx.EndBusyCursor()
        wx.MessageBox(f"Successfully deleted model '{model_name}'!", 
                     "Delete Complete", wx.OK | wx.ICON_INFORMATION)
        
        # Clear current selection since the model is gone
        self.current_model = None
        
        # Disable action buttons
        self.delete_btn.Enable(False)
        
        # Clear details panels
        self.overview_text.SetValue("No model selected.")
        self.capabilities_text.SetValue("No model selected.")
        self.modelfile_text.SetValue("No model selected.")
        
        # Update status bar
        self.status_bar.SetStatusText("No model selected", 1)
        
        # Refresh model list to remove deleted model
        self._load_models_async()
    
    def _on_delete_failure(self, model_name: str, error_message: str) -> None:
        """Handle failed model deletion."""
        wx.EndBusyCursor()
        wx.MessageBox(f"Failed to delete model '{model_name}':\n\n{error_message}", 
                     "Delete Failed", wx.OK | wx.ICON_ERROR)

    def on_tab_changed(self, event: wx.BookCtrlEvent) -> None:
        """Handle notebook tab change events."""
        if not self.current_model or not self.current_model.name or not self.current_model.name.strip():
            return
            
        # Get the newly selected tab
        selection = event.GetSelection()
        
        # Check if the Modelfile tab was selected (index 2: Overview=0, Capabilities=1, Modelfile=2)
        if selection == 2 and not self._modelfile_loaded:
            # Load the modelfile content automatically
            self._load_modelfile(self.current_model.name)
            self._modelfile_loaded = True
        
        event.Skip()  # Allow the event to continue processing

    def _load_modelfile(self, model_name: str) -> None:
        """Load and display the modelfile for the selected model."""
        # Validate model name
        if not model_name or not model_name.strip():
            logger.warning("Cannot load modelfile: model name is empty")
            self.modelfile_text.SetValue("Error: Model name is empty")
            return
            
        # Show loading message
        self.modelfile_text.SetValue("Loading modelfile...")
        
        def load_modelfile_worker():
            """Worker thread function to load modelfile."""
            try:
                # Fetch modelfile from API
                modelfile_content = self.ollama_client.get_modelfile(model_name)
                
                # Update GUI on main thread
                wx.CallAfter(self.modelfile_text.SetValue, modelfile_content)
                
            except Exception as e:
                logger.error(f"Error loading modelfile for {model_name}: {e}")
                error_message = f"Error loading modelfile for {model_name}:\n{str(e)}"
                wx.CallAfter(self.modelfile_text.SetValue, error_message)
        
        # Run in background thread to avoid blocking GUI
        threading.Thread(target=load_modelfile_worker, daemon=True).start()
    
    def on_close(self, event: wx.CloseEvent) -> None:
        """Handle window close event."""
        logger.info("Enhanced main window closing")
        
        # Save current conversation before closing
        try:
            self.save_current_conversation()
        except Exception as e:
            logger.error(f"Error saving conversation on close: {e}")
        
        # Save window state to configuration
        try:
            self._save_window_state()
        except Exception as e:
            logger.error(f"Error saving window state: {e}")
        
        # Close backend connections
        try:
            if hasattr(self, 'db_manager'):
                self.db_manager.close()
        except Exception as e:
            logger.error(f"Error closing database: {e}")
        
        event.Skip()  # Allow the window to close
    
    def _save_window_state(self) -> None:
        """Save current window state to configuration."""
        try:
            # Update window preferences
            size = self.GetSize()
            self.config.ui_preferences.window_width = size.width
            self.config.ui_preferences.window_height = size.height
            self.config.ui_preferences.window_maximized = self.IsMaximized()
            
            # Save configuration
            self.config.save_to_file()
            
            logger.debug(f"Saved window state: {size.width}x{size.height}, maximized={self.IsMaximized()}")
            
        except Exception as e:
            logger.error(f"Error saving window state: {e}")

    def _on_settings(self, event: wx.CommandEvent) -> None:
        """Handle settings menu item."""
        try:
            # Get list of available model names for the dialog
            model_names = [model.name for model in self.models] if self.models else []
            
            # Create and show settings dialog
            dlg = SettingsDialog(self, self.config, model_names)
            if dlg.ShowModal() == wx.ID_OK:
                # Save the updated configuration
                updated_config = dlg.get_config()
                self.config = updated_config
                self.config.save_to_file()
                
                # Apply settings that can be changed immediately
                self._apply_settings_changes()
                
                wx.MessageBox("Settings saved successfully!\nSome changes may require restarting the application.", 
                             "Settings", wx.OK | wx.ICON_INFORMATION)
            
            dlg.Destroy()
            
        except Exception as e:
            logger.error(f"Error opening settings dialog: {e}")
            wx.MessageBox(f"Error opening settings: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def _apply_settings_changes(self) -> None:
        """Apply settings changes that can be applied immediately."""
        try:
            # Auto-select default model if configured
            if (self.config.ui_preferences.auto_select_default_model and 
                self.config.ui_preferences.default_model):
                self._select_default_model()
            
            # Apply chat font settings
            self._apply_chat_font_settings()
            
            # Apply other UI settings
            self._apply_ui_settings()
                
        except Exception as e:
            logger.error(f"Error applying settings changes: {e}")
    
    def _apply_chat_font_settings(self) -> None:
        """Apply chat font size and family settings."""
        try:
            if hasattr(self, 'chat_output') and self.chat_output:
                # Get current font
                current_font = self.chat_output.GetFont()
                
                # Create new font with updated settings
                font_size = self.config.ui_preferences.chat_font_size
                font_family = self.config.ui_preferences.chat_font_family
                
                # Map font family strings to wx constants
                family_map = {
                    "Default": wx.FONTFAMILY_DEFAULT,
                    "Monospace": wx.FONTFAMILY_TELETYPE,
                    "Serif": wx.FONTFAMILY_ROMAN,
                    "Sans-serif": wx.FONTFAMILY_SWISS
                }
                
                wx_family = family_map.get(font_family, wx.FONTFAMILY_DEFAULT)
                
                # Create and set new font
                new_font = wx.Font(
                    font_size, 
                    wx_family, 
                    wx.FONTSTYLE_NORMAL, 
                    wx.FONTWEIGHT_NORMAL
                )
                
                self.chat_output.SetFont(new_font)
                self.chat_output.Refresh()
                
                logger.debug(f"Applied chat font settings: size={font_size}, family={font_family}")
                
        except Exception as e:
            logger.error(f"Error applying chat font settings: {e}")
    
    def _apply_ui_settings(self) -> None:
        """Apply other UI settings that can be changed immediately."""
        try:
            # Apply model list sorting if needed
            self._apply_model_list_sorting()
            
            logger.debug("Applied UI settings")
            
        except Exception as e:
            logger.error(f"Error applying UI settings: {e}")
    
    def _apply_model_list_sorting(self) -> None:
        """Apply model list sorting preferences."""
        try:
            # Note: For full sorting support, we'd need to implement sorting in _update_model_list
            # For now, just log the preference
            sort_column = self.config.ui_preferences.model_list_sort_column
            sort_ascending = self.config.ui_preferences.model_list_sort_ascending
            
            logger.debug(f"Model list sorting preference: {sort_column}, ascending={sort_ascending}")
            
        except Exception as e:
            logger.error(f"Error applying model list sorting: {e}")
    
    def _format_message_for_display(self, message: str, role: str, attached_images: Optional[List[ChatImage]] = None) -> str:
        """Format a message for display in the chat output."""
        try:
            formatted_message = ""
            
            # Add timestamp if enabled
            if self.config.ui_preferences.show_timestamps:
                from datetime import datetime
                timestamp = datetime.now().strftime("%H:%M:%S")
                formatted_message += f"[{timestamp}] "
            
            # Add the message
            formatted_message += f"\n{message}\n"
            
            # Add image info if present
            if attached_images:
                formatted_message += f"📷 Attached {len(attached_images)} image(s): "
                formatted_message += ", ".join([img.filename or "Unknown" for img in attached_images])
                formatted_message += "\n"
            
            return formatted_message
            
        except Exception as e:
            logger.error(f"Error formatting message for display: {e}")
            return f"\n{message}\n"
    
    def _auto_scroll_chat(self) -> None:
        """Auto-scroll chat to bottom if enabled."""
        try:
            if self.config.ui_preferences.auto_scroll_chat and hasattr(self, 'chat_output'):
                self.chat_output.SetInsertionPointEnd()
                
        except Exception as e:
            logger.error(f"Error auto-scrolling chat: {e}")

    def _select_default_model(self) -> None:
        """Select the configured default model if available."""
        try:
            default_model_name = self.config.ui_preferences.default_model
            if not default_model_name:
                return
                
            # Find the model in the list
            for i in range(self.model_list.GetItemCount()):
                item_name = self.model_list.GetItemText(i, 1)  # Name is in column 1
                if item_name == default_model_name:
                    # Select the model
                    self.model_list.Select(i)
                    self.model_list.EnsureVisible(i)
                    
                    # Find the model object and set it as current
                    for model in self.models:
                        if model.name == default_model_name:
                            self.current_model = model
                            self._update_model_details()
                            self.status_bar.SetStatusText(f"Selected: {model.name}", 1)
                            break
                    break
                    
        except Exception as e:
            logger.error(f"Error selecting default model: {e}")
    

    def _on_exit(self, event: wx.CommandEvent) -> None:
        """Handle exit menu item."""
        self.Close()

    def _on_refresh_models(self, event: wx.CommandEvent) -> None:
        """Handle refresh models menu item."""
        # Use the same async refresh as the button
        self.on_refresh(event)

    def _on_about(self, event: wx.CommandEvent) -> None:
        """Handle about menu item."""
        info = wx.adv.AboutDialogInfo()
        info.SetName("LlamaLot")
        info.SetVersion("1.0.0")
        info.SetDescription("Enhanced Ollama Model Manager\n\nA comprehensive tool for managing and interacting with Ollama models.")
        info.SetCopyright("© 2024")
        info.AddDeveloper("LlamaLot Development Team")
        
        wx.adv.AboutBox(info)

    # Chat History Methods
    def refresh_conversation_list(self) -> None:
        """Refresh the conversation list from the database."""
        try:
            # Clear existing items
            self.conversation_list.DeleteAllItems()
            
            # Get conversations from database - returns tuples of (conversation_id, title, updated_at)
            conversations = self.db_manager.list_conversations(limit=100)
            
            # Store conversation IDs for lookup
            self.conversation_ids = []
            
            # Populate the list
            for i, (conv_id, title, updated_at) in enumerate(conversations):
                # Use the actual title from database, or generate a fallback
                display_title = title or f"Conversation {conv_id}"
                index = self.conversation_list.InsertItem(i, display_title)
                
                # Store conversation ID in our lookup list
                self.conversation_ids.append(conv_id)
                
                # Get full conversation to get model name and message count
                full_conv = self.db_manager.get_conversation(conv_id)
                if full_conv:
                    self.conversation_list.SetItem(index, 1, full_conv.model_name or "Unknown")
                    self.conversation_list.SetItem(index, 2, str(len(full_conv.messages)))
                else:
                    self.conversation_list.SetItem(index, 1, "Unknown")
                    self.conversation_list.SetItem(index, 2, "0")
                
                # Format creation date
                if updated_at:
                    date_str = updated_at.strftime("%Y-%m-%d %H:%M")
                    self.conversation_list.SetItem(index, 3, date_str)
            
            logger.info(f"Loaded {len(conversations)} conversations in history")
            
        except Exception as e:
            logger.error(f"Error refreshing conversation list: {e}")
            wx.MessageBox(f"Error loading conversation history: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def on_refresh_history(self, event: wx.CommandEvent) -> None:
        """Handle refresh history button click."""
        self.refresh_conversation_list()

    def on_conversation_selected(self, event: wx.ListEvent) -> None:
        """Handle conversation selection."""
        try:
            index = event.GetIndex()
            
            # Get conversation ID from our lookup list
            if hasattr(self, 'conversation_ids') and 0 <= index < len(self.conversation_ids):
                conv_id = self.conversation_ids[index]
            else:
                logger.error(f"Invalid conversation index: {index}")
                return
            
            # Load and display the conversation
            conversation = self.db_manager.get_conversation(conv_id)
            if conversation:
                self.display_conversation(conversation)
                self.delete_conversation_btn.Enable(True)
                # Store the current conversation ID for deletion
                self.selected_conversation_id = conv_id
            
        except Exception as e:
            logger.error(f"Error loading conversation: {e}")
            wx.MessageBox(f"Error loading conversation: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def on_conversation_deselected(self, event: wx.ListEvent) -> None:
        """Handle conversation deselection."""
        self.conversation_display.SetValue("")
        self.delete_conversation_btn.Enable(False)
        self.selected_conversation_id = None

    def on_delete_conversation(self, event: wx.CommandEvent) -> None:
        """Handle delete conversation button click."""
        try:
            if not hasattr(self, 'selected_conversation_id') or not self.selected_conversation_id:
                return
                
            conv_id = self.selected_conversation_id
            selected = self.conversation_list.GetFirstSelected()
            conv_title = self.conversation_list.GetItemText(selected) if selected != -1 else "Unknown"
            
            # Confirm deletion
            dlg = wx.MessageDialog(
                self,
                f"Are you sure you want to delete the conversation '{conv_title}'?\n\nThis action cannot be undone.",
                "Confirm Deletion",
                wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION
            )
            
            if dlg.ShowModal() == wx.ID_YES:
                # Delete from database
                self.db_manager.delete_conversation(conv_id)
                
                # Refresh the list
                self.refresh_conversation_list()
                
                # Clear the display
                self.conversation_display.SetValue("")
                self.delete_conversation_btn.Enable(False)
                self.selected_conversation_id = None
                
                logger.info(f"Deleted conversation {conv_id}: {conv_title}")
                
            dlg.Destroy()
            
        except Exception as e:
            logger.error(f"Error deleting conversation: {e}")
            wx.MessageBox(f"Error deleting conversation: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def display_conversation(self, conversation: ChatConversation) -> None:
        """Display a conversation in the viewer."""
        try:
            self.conversation_display.SetValue("")
            
            # Set up text styles
            self.conversation_display.SetDefaultStyle(wx.TextAttr(wx.Colour(50, 50, 50)))
            
            # Add conversation header
            header = f"Conversation: {conversation.title or f'ID {conversation.conversation_id}'}\n"
            header += f"Model: {conversation.model_name}\n"
            if conversation.created_at:
                header += f"Created: {conversation.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            header += f"Messages: {len(conversation.messages)}\n"
            header += "=" * 50 + "\n\n"
            
            self.conversation_display.SetDefaultStyle(wx.TextAttr(wx.Colour(0, 0, 150), font=wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)))
            self.conversation_display.AppendText(header)
            
            # Add messages
            for i, message in enumerate(conversation.messages):
                # Message header
                if message.role == MessageRole.USER:
                    self.conversation_display.SetDefaultStyle(wx.TextAttr(wx.Colour(0, 100, 0), font=wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)))
                    self.conversation_display.AppendText("👤 User:\n")
                elif message.role == MessageRole.ASSISTANT:
                    self.conversation_display.SetDefaultStyle(wx.TextAttr(wx.Colour(150, 0, 0), font=wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)))
                    self.conversation_display.AppendText("🤖 Assistant:\n")
                else:
                    self.conversation_display.SetDefaultStyle(wx.TextAttr(wx.Colour(100, 100, 100), font=wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)))
                    self.conversation_display.AppendText(f"[{message.role.value}]:\n")
                
                # Message content
                self.conversation_display.SetDefaultStyle(wx.TextAttr(wx.Colour(50, 50, 50)))
                self.conversation_display.AppendText(f"{message.content}\n")
                
                # Add spacing between messages
                if i < len(conversation.messages) - 1:
                    self.conversation_display.AppendText("\n" + "-" * 40 + "\n\n")
            
            # Scroll to top
            self.conversation_display.SetInsertionPoint(0)
            
        except Exception as e:
            logger.error(f"Error displaying conversation: {e}")
            self.conversation_display.SetValue(f"Error loading conversation: {e}")
