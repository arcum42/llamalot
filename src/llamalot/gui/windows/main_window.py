"""
Main window for LlamaLot application.

Contains the main GUI interface for managing Ollama models with
backend integration.
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
from llamalot.gui.managers.backend_manager import BackendManager
from llamalot.gui.managers.menu_manager import MenuManager
from llamalot.gui.managers.layout_manager import LayoutManager
from llamalot.gui.managers.tab_manager import TabManager
from llamalot.models import OllamaModel, ApplicationConfig, MessageRole
from llamalot.models.chat import ChatConversation, ChatMessage, ChatImage, MessageRole
from llamalot.gui.dialogs.image_viewer_dialog import ImageViewerDialog
from llamalot.gui.dialogs.model_pull_progress_dialog import ModelPullProgressDialog
from llamalot.gui.dialogs.settings_dialog import SettingsDialog
from llamalot.gui.dialogs.create_model_dialog import CreateModelDialog
from llamalot.gui.components.image_attachment_panel import ImageAttachmentPanel
from llamalot.gui.components.embeddings_panel import EmbeddingsPanel
from llamalot.gui.tabs.history_tab import HistoryTab
from llamalot.gui.tabs.embeddings_tab import EmbeddingsTab
from llamalot.gui.tabs.batch_tab import BatchTab
from llamalot.gui.tabs.chat_tab import ChatTab
from llamalot.gui.tabs.models_tab import ModelsTab

logger = get_logger(__name__)


class MainWindow(wx.Frame):
    """Main application window with backend integration."""
    
    def __init__(self):
        """Initialize the main window."""
        # Initialize backend manager
        logger.info("Initializing main window")
        self.backend_manager = BackendManager()
        self._init_backend()
        
        # Initialize menu manager
        self.menu_manager = MenuManager(self)
        
        # Initialize layout manager
        self.layout_manager = LayoutManager(self)
        
        # Initialize tab manager (will be configured after layout creation)
        self.tab_manager = None
        
        # Use configuration for window size
        initial_size = wx.Size(
            self.config.ui_preferences.window_width,
            self.config.ui_preferences.window_height
        )
        
        super().__init__(
            parent=None,
            title="LlamaLot - Ollama Model Manager",
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
        self.current_model: Optional[OllamaModel] = None
        
        self.current_conversation: Optional[ChatConversation] = None
        
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
        
        logger.info("Main window initialized successfully")
    
    def _init_backend(self) -> None:
        """Initialize backend components using BackendManager."""
        try:
            if not self.backend_manager.initialize():
                wx.MessageBox(
                    "Failed to initialize backend components", 
                    "Initialization Error", 
                    wx.OK | wx.ICON_ERROR
                )
                return
            
            # Set convenience properties for compatibility
            self.config = self.backend_manager.config
            self.ollama_client = self.backend_manager.ollama_client
            self.cache_manager = self.backend_manager.cache_manager
            self.db_manager = self.backend_manager.db_manager
            
            logger.info("Backend components initialized successfully via BackendManager")
            
        except Exception as e:
            logger.error(f"Failed to initialize backend: {e}")
            wx.MessageBox(
                f"Failed to initialize backend components:\n{str(e)}", 
                "Initialization Error", 
                wx.OK | wx.ICON_ERROR
            )
    
    def _create_main_layout(self) -> None:
        """Create the main layout using LayoutManager."""
        # Create layout using the manager
        self.layout_manager.create_main_layout()
        
        # Get references to components created by the layout manager
        self.main_panel = self.layout_manager.main_panel
        self.notebook = self.layout_manager.notebook
        self.status_bar = self.layout_manager.status_bar
        
        # Initialize and configure tab manager
        self.tab_manager = TabManager(self, self.notebook)
        self.tab_manager.set_backend_components(
            self.ollama_client,
            self.cache_manager,
            self.db_manager,
            self.config
        )
        
        # Create all tabs using the tab manager
        self.tab_manager.create_all_tabs()
        
        # Get references to the created tabs
        self.models_tab = self.tab_manager.models_tab
        self.chat_tab = self.tab_manager.chat_tab
        self.batch_tab = self.tab_manager.batch_tab
        self.embeddings_tab = self.tab_manager.embeddings_tab
        self.history_tab = self.tab_manager.history_tab
        
    def _create_menu_bar(self) -> None:
        """Create the menu bar using MenuManager."""
        # Create menu bar using the manager
        menu_bar = self.menu_manager.create_menu_bar()
        self.SetMenuBar(menu_bar)
        
        # Bind menu events
        event_handlers = {
            wx.ID_PREFERENCES: self._on_settings,
            wx.ID_EXIT: self._on_exit,
            wx.ID_REFRESH: self._on_refresh_models,
            "Pull Model...": self._on_pull_model,
            "Create Model...": self._on_create_model,
            "Delete Model...": self._on_delete_model,
            "New Chat": self.on_new_chat,
            "Export Chat...": self._on_export_chat,
            # Edit menu (Undo/Redo are disabled, so no handlers needed)
            wx.ID_CUT: self._on_cut,
            wx.ID_COPY: self._on_copy,
            wx.ID_PASTE: self._on_paste,
            # View menu
            "Models Tab": self._on_switch_to_models_tab,
            "Chat Tab": self._on_switch_to_chat_tab,
            "Batch Tab": self._on_switch_to_batch_tab,
            "Embeddings Tab": self._on_switch_to_embeddings_tab,
            "History Tab": self._on_switch_to_history_tab,
            "Refresh All": self._on_refresh_all,
            "Toggle Fullscreen": self._on_toggle_fullscreen,
            wx.ID_ABOUT: self._on_about,
        }
        
        self.menu_manager.bind_menu_events(event_handlers)
        
    def get_embeddings_context(self, query: str, max_results: int = 3) -> List:
        """
        Get embeddings context for chat integration.
        
        Args:
            query: The user's query to search for relevant context
            max_results: Maximum number of context results to return
            
        Returns:
            List of relevant document excerpts for context
        """
        try:
            if hasattr(self, 'embeddings_tab') and self.embeddings_tab:
                return self.embeddings_tab.get_embeddings_context(query, max_results)
            return []
        except Exception as e:
            logger.error(f"Error getting embeddings context: {e}")
            return []
    
    def _on_refresh_models(self, event: wx.CommandEvent) -> None:
        """Delegate refresh models to the models tab."""
        if hasattr(self, 'models_tab'):
            self.models_tab.on_refresh(event)
    
    def _on_pull_model(self, event: wx.CommandEvent) -> None:
        """Handle pull model menu item."""
        if hasattr(self, 'models_tab') and self.models_tab:
            self.models_tab.on_pull_model(event)
        else:
            self.on_pull_model(event)

    def _on_create_model(self, event: wx.CommandEvent) -> None:
        """Handle create model menu item."""
        if hasattr(self, 'models_tab') and self.models_tab:
            self.models_tab.on_create_model(event)
        else:
            self.on_create_model(event)

    def _on_delete_model(self, event: wx.CommandEvent) -> None:
        """Handle delete model menu item."""
        if hasattr(self, 'models_tab') and self.models_tab:
            self.models_tab.on_delete_model(event)
        else:
            self.on_delete_model(event)

    def _on_export_chat(self, event: wx.CommandEvent) -> None:
        """Handle export chat menu item."""
        try:
            # Get the current tab
            current_tab = self.notebook.GetSelection()
            
            if current_tab == 1:  # Chat tab
                # Export current conversation from chat tab
                if hasattr(self, 'chat_tab') and self.chat_tab:
                    self._export_current_chat()
            elif current_tab == 2:  # History tab  
                # Use history tab's export functionality
                if hasattr(self, 'history_tab') and self.history_tab:
                    self.history_tab.on_export_chat(event)
            else:
                # If not on chat or history tab, try to export current chat anyway
                self._export_current_chat()
                
        except Exception as e:
            logger.error(f"Error exporting chat: {e}")
            wx.MessageBox(f"Error exporting chat: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def _export_current_chat(self) -> None:
        """Export the current conversation from chat tab."""
        try:
            if not hasattr(self, 'chat_tab') or not self.chat_tab:
                wx.MessageBox("Chat tab not available", "Error", wx.OK | wx.ICON_ERROR)
                return
                
            # Get current conversation from chat tab
            if not hasattr(self.chat_tab, 'current_conversation') or not self.chat_tab.current_conversation:
                wx.MessageBox("No active conversation to export", "Info", wx.OK | wx.ICON_INFORMATION)
                return
                
            conversation = self.chat_tab.current_conversation
            
            # Create safe filename from conversation title
            title = conversation.title or f"conversation_{conversation.conversation_id[:8]}"
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            if not safe_title:
                safe_title = f"current_chat_{conversation.conversation_id[:8]}"
            
            # Show format selection dialog
            format_dlg = wx.SingleChoiceDialog(
                self,
                "Choose export format:",
                "Export Format",
                ["Text (.txt)", "Markdown (.md)"]
            )
            
            if format_dlg.ShowModal() != wx.ID_OK:
                format_dlg.Destroy()
                return
                
            format_choice = format_dlg.GetSelection()
            format_dlg.Destroy()
            
            # Determine file extension and default filename
            if format_choice == 0:  # Text
                extension = ".txt"
                default_filename = f"{safe_title}.txt"
            else:  # Markdown
                extension = ".md"
                default_filename = f"{safe_title}.md"
            
            # Show file save dialog
            with wx.FileDialog(
                self,
                f"Export conversation as {extension[1:].upper()}",
                defaultFile=default_filename,
                wildcard=f"{extension[1:].upper()} files (*{extension})|*{extension}|All files (*.*)|*.*",
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
            ) as save_dlg:
                
                if save_dlg.ShowModal() == wx.ID_OK:
                    filepath = save_dlg.GetPath()
                    
                    # Use the same export methods as history tab
                    if hasattr(self, 'history_tab') and self.history_tab:
                        if format_choice == 0:  # Text format
                            self.history_tab._export_as_text(conversation, filepath)
                        else:  # Markdown format
                            self.history_tab._export_as_markdown(conversation, filepath)
                    else:
                        # Fallback basic export
                        self._basic_export_conversation(conversation, filepath, format_choice == 1)
                    
                    logger.info(f"Exported current conversation to {filepath}")
                    wx.MessageBox(
                        f"Conversation exported successfully to:\n{filepath}",
                        "Export Complete",
                        wx.OK | wx.ICON_INFORMATION
                    )
                    
        except Exception as e:
            logger.error(f"Error exporting current chat: {e}")
            wx.MessageBox(f"Error exporting conversation: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def _basic_export_conversation(self, conversation, filepath: str, is_markdown: bool = False) -> None:
        """Basic fallback method to export conversation."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                if is_markdown:
                    f.write(f"# {conversation.title or 'Chat Conversation'}\n\n")
                    f.write(f"**Model:** {conversation.model_name or 'Unknown'}  \n\n")
                    f.write("---\n\n")
                    
                    for i, message in enumerate(conversation.messages):
                        if message.role.value == 'user':
                            f.write("## 👤 User\n\n")
                        elif message.role.value == 'assistant':
                            f.write("## 🤖 Assistant\n\n")
                        else:
                            f.write(f"## [{message.role.value}]\n\n")
                        
                        f.write(f"{message.content.strip()}\n\n")
                        if i < len(conversation.messages) - 1:
                            f.write("---\n\n")
                else:
                    f.write(f"Conversation: {conversation.title or 'Chat Conversation'}\n")
                    f.write(f"Model: {conversation.model_name or 'Unknown'}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for i, message in enumerate(conversation.messages):
                        if message.role.value == 'user':
                            f.write("User:\n")
                        elif message.role.value == 'assistant':
                            f.write("Assistant:\n")
                        else:
                            f.write(f"[{message.role.value}]:\n")
                        
                        f.write(f"{message.content}\n")
                        if i < len(conversation.messages) - 1:
                            f.write("\n" + "-" * 40 + "\n\n")
                            
        except Exception as e:
            logger.error(f"Error writing export file: {e}")
            raise
    
    # Edit menu handlers
    def _on_cut(self, event: wx.CommandEvent) -> None:
        """Handler for Cut menu item"""
        focus_window = wx.Window.FindFocus()
        if focus_window and hasattr(focus_window, 'CanCut') and focus_window.CanCut():
            focus_window.Cut()

    def _on_copy(self, event: wx.CommandEvent) -> None:
        """Handler for Copy menu item"""
        focus_window = wx.Window.FindFocus()
        if focus_window and hasattr(focus_window, 'CanCopy') and focus_window.CanCopy():
            focus_window.Copy()

    def _on_paste(self, event: wx.CommandEvent) -> None:
        """Handler for Paste menu item with smart image detection"""
        focus_window = wx.Window.FindFocus()
        
        # Check if we have an image on the clipboard
        if wx.TheClipboard.Open():
            try:
                if wx.TheClipboard.IsSupported(wx.DataFormat(wx.DF_BITMAP)):
                    # We have an image on clipboard - check if we're in the chat tab
                    current_tab = self.notebook.GetSelection()
                    if current_tab == 1 and hasattr(self, 'chat_tab') and self.chat_tab:  # Chat tab
                        # We're in chat tab - try to add image
                        bitmap_data = wx.BitmapDataObject()
                        if wx.TheClipboard.GetData(bitmap_data):
                            bitmap = bitmap_data.GetBitmap()
                            if bitmap.IsOk():
                                # Convert bitmap to temporary file and add to chat
                                self._add_clipboard_image_to_chat(bitmap)
                                wx.TheClipboard.Close()
                                return
                
                # Fall back to regular paste if not image or not in chat tab
                if focus_window and hasattr(focus_window, 'CanPaste') and focus_window.CanPaste():
                    focus_window.Paste()
                    
            finally:
                wx.TheClipboard.Close()
        else:
            # Clipboard not available, try regular paste
            if focus_window and hasattr(focus_window, 'CanPaste') and focus_window.CanPaste():
                focus_window.Paste()

    # View menu handlers
    def _on_switch_to_models_tab(self, event: wx.CommandEvent) -> None:
        """Switch to Models tab (Ctrl+1)"""
        if hasattr(self, 'notebook') and self.notebook:
            self.notebook.SetSelection(0)  # Models is first tab

    def _on_switch_to_chat_tab(self, event: wx.CommandEvent) -> None:
        """Switch to Chat tab (Ctrl+2)"""
        if hasattr(self, 'notebook') and self.notebook:
            self.notebook.SetSelection(1)  # Chat is second tab

    def _on_switch_to_batch_tab(self, event: wx.CommandEvent) -> None:
        """Switch to Batch tab (Ctrl+3)"""
        if hasattr(self, 'notebook') and self.notebook:
            self.notebook.SetSelection(2)  # Batch is third tab

    def _on_switch_to_embeddings_tab(self, event: wx.CommandEvent) -> None:
        """Switch to Embeddings tab (Ctrl+4)"""
        if hasattr(self, 'notebook') and self.notebook:
            self.notebook.SetSelection(3)  # Embeddings is fourth tab

    def _on_switch_to_history_tab(self, event: wx.CommandEvent) -> None:
        """Switch to History tab (Ctrl+5)"""
        if hasattr(self, 'notebook') and self.notebook:
            self.notebook.SetSelection(4)  # History is fifth tab

    def _on_refresh_all(self, event: wx.CommandEvent) -> None:
        """Refresh all data (F5)"""
        try:
            # Refresh models
            if hasattr(self, 'models_tab') and self.models_tab:
                self.models_tab.refresh_models()
            
            # Refresh history
            if hasattr(self, 'history_tab') and self.history_tab:
                self.history_tab.refresh_conversation_list()
                
            # Refresh embeddings collections (use the panel's method)
            if hasattr(self, 'embeddings_tab') and self.embeddings_tab:
                if hasattr(self.embeddings_tab, 'embeddings_panel') and self.embeddings_tab.embeddings_panel:
                    self.embeddings_tab.embeddings_panel._refresh_collections()
                
            # Show status message
            if hasattr(self, 'status_bar') and self.status_bar:
                self.status_bar.SetStatusText("All data refreshed", 0)
                wx.CallLater(3000, lambda: self.status_bar.SetStatusText("", 0) if self.status_bar else None)
                
        except Exception as e:
            logger.error(f"Error refreshing all data: {e}")
            wx.MessageBox(f"Error refreshing data: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)

    def _on_toggle_fullscreen(self, event: wx.CommandEvent) -> None:
        """Toggle fullscreen mode (F11)"""
        try:
            self.ShowFullScreen(not self.IsFullScreen())
        except Exception as e:
            logger.error(f"Error toggling fullscreen: {e}")
            wx.MessageBox(f"Error toggling fullscreen: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)

    # Tools menu handlers
    def _add_clipboard_image_to_chat(self, bitmap: wx.Bitmap) -> None:
        """Helper method to add clipboard image to chat"""
        try:
            import tempfile
            import os
            
            # Create temporary file
            temp_dir = tempfile.gettempdir()
            temp_filename = f"clipboard_image_{wx.GetUTCTimeMillis()}.png"
            temp_path = os.path.join(temp_dir, temp_filename)
            
            # Save bitmap to temporary file
            bitmap.SaveFile(temp_path, wx.BITMAP_TYPE_PNG)
            
            # Add to chat's image panel if it exists
            if hasattr(self.chat_tab, 'image_panel') and self.chat_tab.image_panel:
                # Add the image path to the panel
                self.chat_tab.image_panel.add_images_from_paths([temp_path])
                
                # Show a brief message
                wx.CallAfter(lambda: wx.MessageBox("Image from clipboard added to chat", "Success", 
                                                 wx.OK | wx.ICON_INFORMATION))
            else:
                logger.warning("Chat tab or image panel not available for clipboard image")
                wx.MessageBox("Chat image panel not available", "Warning", wx.OK | wx.ICON_WARNING)
            
        except Exception as e:
            logger.error(f"Failed to add clipboard image: {e}")
            wx.MessageBox(f"Failed to add clipboard image: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
    

    

    
    def _create_models_details_panel(self) -> None:
        """Create the model details and management panel for the models tab."""
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Model Management section
        mgmt_label = wx.StaticText(self.models_right_panel, label="Model Management")
        mgmt_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        
        # Model actions buttons
        action_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.models_pull_btn = wx.Button(self.models_right_panel, label="Pull Model", size=wx.Size(80, 25))
        self.models_create_btn = wx.Button(self.models_right_panel, label="Create Model", size=wx.Size(100, 25))
        self.models_delete_btn = wx.Button(self.models_right_panel, label="Delete", size=wx.Size(80, 25))
        
        # Initially disable action buttons until a model is selected
        self.models_delete_btn.Enable(False)
        
        action_sizer.Add(self.models_pull_btn, 0, wx.RIGHT, 5)
        action_sizer.Add(self.models_create_btn, 0, wx.RIGHT, 5)
        action_sizer.Add(self.models_delete_btn, 0)
        
        # Chat actions section
        chat_label = wx.StaticText(self.models_right_panel, label="Chat Actions")
        chat_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        
        chat_action_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.models_new_chat_btn = wx.Button(self.models_right_panel, label="New Chat", size=wx.Size(100, 30))
        self.models_new_chat_btn.SetToolTip("Start a new chat with the highlighted model")
        self.models_new_chat_btn.Enable(False)  # Initially disabled until a model is selected
        
        chat_action_sizer.Add(self.models_new_chat_btn, 0)
        
        # Model details section with tabs
        info_label = wx.StaticText(self.models_right_panel, label="Model Information")
        info_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        
        self.models_details_notebook = wx.Notebook(self.models_right_panel)
        
        # Overview tab
        self.models_overview_panel = wx.Panel(self.models_details_notebook)
        self.models_overview_text = wx.TextCtrl(
            self.models_overview_panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY,
            size=wx.Size(-1, 200)
        )
        self.models_overview_text.SetValue("Select a model to view details...")
        overview_sizer = wx.BoxSizer(wx.VERTICAL)
        overview_sizer.Add(self.models_overview_text, 1, wx.EXPAND | wx.ALL, 5)
        self.models_overview_panel.SetSizer(overview_sizer)
        
        # Capabilities tab
        self.models_capabilities_panel = wx.Panel(self.models_details_notebook)
        self.models_capabilities_text = wx.TextCtrl(
            self.models_capabilities_panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY,
            size=wx.Size(-1, 200)
        )
        models_capabilities_sizer = wx.BoxSizer(wx.VERTICAL)
        models_capabilities_sizer.Add(self.models_capabilities_text, 1, wx.EXPAND | wx.ALL, 5)
        self.models_capabilities_panel.SetSizer(models_capabilities_sizer)
        
        # Modelfile tab
        self.models_modelfile_panel = wx.Panel(self.models_details_notebook)
        self.models_modelfile_text = wx.TextCtrl(
            self.models_modelfile_panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY,
            size=wx.Size(-1, 200)
        )
        models_modelfile_sizer = wx.BoxSizer(wx.VERTICAL)
        models_modelfile_sizer.Add(self.models_modelfile_text, 1, wx.EXPAND | wx.ALL, 5)
        self.models_modelfile_panel.SetSizer(models_modelfile_sizer)
        
        # Add tabs to notebook
        self.models_details_notebook.AddPage(self.models_overview_panel, "Overview")
        self.models_details_notebook.AddPage(self.models_capabilities_panel, "Capabilities")
        self.models_details_notebook.AddPage(self.models_modelfile_panel, "Modelfile")
        
        # Add to main sizer
        sizer.Add(mgmt_label, 0, wx.ALL, 10)
        sizer.Add(action_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        sizer.Add(chat_label, 0, wx.ALL, 10)
        sizer.Add(chat_action_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        sizer.Add(info_label, 0, wx.ALL, 10)
        sizer.Add(self.models_details_notebook, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
        self.models_right_panel.SetSizer(sizer)
    
    
    def _bind_events(self) -> None:
        """Bind event handlers."""        
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
            
            # Delegate model loading to the models tab
            if hasattr(self, 'models_tab'):
                self.models_tab.refresh_models()
            
            # Auto-select default model if configured
            if (self.config.ui_preferences.auto_select_default_model and 
                self.config.ui_preferences.default_model and 
                not self.current_model):  # Only auto-select if no model is currently selected
                self._select_default_model()
            
            self.status_bar.SetStatusText("Ready", 0)
            
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            self.status_bar.SetStatusText("Error loading models", 0)
            wx.MessageBox(
                f"Failed to load models:\n{str(e)}", 
                "Error", 
                wx.OK | wx.ICON_ERROR
            )
    

    
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
                    self.models_list.Select(i)
                    self.models_list.EnsureVisible(i)
                    
                    # Trigger the selection event manually to update UI
                    self.current_model = model
                    self.models_delete_btn.Enable(True)
                    self._update_model_details()
                    self.chat_tab.set_current_model(self.current_model)
                    self.chat_tab.start_new_conversation()
                    
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
        self.models_refresh_btn.Enable(False)
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
        self.models_refresh_btn.Enable(True)
        
        if error:
            logger.error(f"Failed to refresh models: {error}")
            self.status_bar.SetStatusText("Error refreshing models", 0)
            wx.MessageBox(
                f"Failed to refresh models:\n{str(error)}", 
                "Refresh Error", 
                wx.OK | wx.ICON_ERROR
            )
        elif models is not None:
            # Update model list through the models tab
            if hasattr(self, 'models_tab'):
                self.models_tab.refresh_models()
            
            self.status_bar.SetStatusText("Ready", 0)
            
            logger.info("Manual refresh completed successfully")
    

    

    

    

    
    def _update_model_details(self) -> None:
        """Update the model details for the current chat model (Chat tab only)."""
        if not self.current_model:
            return
        
        # Update selected model display in chat tab
        self.chat_tab.set_current_model(self.current_model)
        
        # Reset modelfile loaded flag for new model
        self._modelfile_loaded = False
    


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
                if hasattr(self, 'history_tab'):
                    wx.CallAfter(self.history_tab.refresh_conversation_list)
                
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
            # Delegate to chat tab if available
            if hasattr(self, 'chat_tab') and self.chat_tab:
                self.chat_tab.on_new_chat(event)
                
                # Switch to chat tab to show the new conversation
                if hasattr(self, 'notebook') and self.notebook:
                    self.notebook.SetSelection(1)  # Chat tab is index 1
            else:
                wx.MessageBox("Chat functionality not available.", "Error", wx.OK | wx.ICON_ERROR)
                
        except Exception as e:
            logger.error(f"Error starting new chat: {e}")
            wx.MessageBox(f"Error starting new chat: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def on_models_new_chat(self, event: wx.CommandEvent) -> None:
        """Handle new chat button click from Models tab."""
        try:
            if self.highlighted_model:
                # Set the highlighted model as the current chat model
                self.current_model = self.highlighted_model
                
                # Save current conversation if it exists and has messages
                self.chat_tab.save_current_conversation()
                
                # Switch to Chat tab
                self.notebook.SetSelection(1)  # Chat tab is index 1
                
                # Clear the chat display
                self.chat_tab.clear_chat()
                
                # Update chat model display
                self.chat_tab.set_current_model(self.current_model)
                
                # Start a new conversation with the selected model
                self.chat_tab.start_new_conversation()
                logger.info(f"Started new chat with {self.highlighted_model.name} from Models tab")
                
                # Update status
                self.status_bar.SetStatusText(f"New chat started with {self.highlighted_model.name}", 0)
            else:
                wx.MessageBox("Please select a model first.", "No Model Selected", wx.OK | wx.ICON_WARNING)
                
        except Exception as e:
            logger.error(f"Error starting new chat from Models tab: {e}")

    def on_model_double_click(self, event: wx.ListEvent) -> None:
        """Handle double-click on model in Models tab."""
        try:
            if self.highlighted_model:
                # Set the highlighted model as the current chat model
                self.current_model = self.highlighted_model
                
                # Save current conversation if it exists and has messages
                self.chat_tab.save_current_conversation()
                
                # Switch to Chat tab
                self.notebook.SetSelection(1)  # Chat tab is index 1
                
                # Clear the chat display
                self.chat_tab.clear_chat()
                
                # Update chat model display
                self.chat_tab.set_current_model(self.current_model)
                
                # Start a new conversation with the selected model
                self.chat_tab.start_new_conversation()
                logger.info(f"Started new chat with {self.highlighted_model.name} via double-click")
                
                # Update status
                self.status_bar.SetStatusText(f"New chat started with {self.highlighted_model.name}", 0)
            else:
                wx.MessageBox("Please select a model first.", "No Model Selected", wx.OK | wx.ICON_WARNING)
                
        except Exception as e:
            logger.error(f"Error starting new chat via double-click: {e}")
            wx.MessageBox(f"Error starting new chat: {e}", "Error", wx.OK | wx.ICON_ERROR)
    
    def _refresh_model_running_status(self) -> None:
        """Refresh only the running status of models without full reload."""
        try:
            # Delegate to models tab to refresh models (which includes running status)
            if hasattr(self, 'models_tab'):
                self.models_tab.refresh_models()
                logger.info("Delegated model refresh to models tab")
            
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
        self.models_delete_btn.Enable(False)
        
        # Clear details panels
        self.models_overview_text.SetValue("No model selected.")
        self.models_capabilities_text.SetValue("No model selected.")
        self.models_modelfile_text.SetValue("No model selected.")
        
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
            self.models_modelfile_text.SetValue("Error: Model name is empty")
            return
            
        # Show loading message
        self.models_modelfile_text.SetValue("Loading modelfile...")
        
        def load_modelfile_worker():
            """Worker thread function to load modelfile."""
            try:
                # Fetch modelfile from API
                modelfile_content = self.ollama_client.get_modelfile(model_name)
                
                # Update GUI on main thread
                wx.CallAfter(self.models_modelfile_text.SetValue, modelfile_content)
                
            except Exception as e:
                logger.error(f"Error loading modelfile for {model_name}: {e}")
                error_message = f"Error loading modelfile for {model_name}:\n{str(e)}"
                wx.CallAfter(self.models_modelfile_text.SetValue, error_message)
        
        # Run in background thread to avoid blocking GUI
        threading.Thread(target=load_modelfile_worker, daemon=True).start()
    
    def on_close(self, event: wx.CloseEvent) -> None:
        """Handle window close event."""
        logger.info("Main window closing")
        
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
            if hasattr(self, 'backend_manager') and self.backend_manager:
                self.backend_manager.cleanup()
        except Exception as e:
            logger.error(f"Error during backend cleanup: {e}")
        
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
            models = self.cache_manager.get_models() if self.cache_manager else []
            model_names = [model.name for model in models]
            
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
            # Delegate to models tab to select the default model
            if hasattr(self, 'models_tab'):
                self.models_tab._select_default_model()
                logger.info("Delegated default model selection to models tab")
                
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
