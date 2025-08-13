"""
Models Tab component for the LlamaLot application.

This module contains the ModelsTab class which handles all model management functionality including:
- Model list display with sorting and filtering
- Model details view with overview (including capabilities) and modelfile information
- Model management actions (pull, create, delete)
- Model selection and highlighting
- Chat integration (new chat with selected model)
"""

import wx
import wx.lib.scrolledpanel
import threading
from typing import Optional, List
from logging import getLogger

from llamalot.models.ollama_model import OllamaModel
from llamalot.gui.dialogs.create_model_dialog import CreateModelDialog

logger = getLogger(__name__)


class ModelsTab(wx.lib.scrolledpanel.ScrolledPanel):
    """Models tab component for managing Ollama models."""
    
    def __init__(self, parent: wx.Window, main_window):
        """Initialize the Models tab.
        
        Args:
            parent: Parent window
            main_window: Reference to the main window for access to managers and functionality
        """
        super().__init__(parent)
        self.SetupScrolling()
        self.main_window = main_window
        
        # Model state
        self.models: List[OllamaModel] = []
        self.highlighted_model: Optional[OllamaModel] = None
        self._modelfile_loaded = False
        
        # Sorting state
        self.sort_column = 1  # Default to Name column
        self.sort_ascending = True
        
        # Create the UI
        self._create_models_ui()
        self._bind_events()
        
        # Load models initially
        self._load_models_async()
        
        logger.info("Models tab created successfully")
    
    def _create_models_ui(self) -> None:
        """Create the models tab UI."""
        # Create main splitter (horizontal - left/right) for models tab
        models_splitter = wx.SplitterWindow(
            self, 
            style=wx.SP_3D | wx.SP_LIVE_UPDATE
        )
        models_splitter.SetMinimumPaneSize(250)
        
        # Create left panel (model list)
        self.models_left_panel = wx.Panel(models_splitter)
        self._create_models_list_panel()
        
        # Create right panel (model management and details)
        self.models_right_panel = wx.Panel(models_splitter)
        self._create_models_details_panel()
        
        # Split the main window - larger left panel to show all model columns
        models_splitter.SplitVertically(self.models_left_panel, self.models_right_panel, 600)
        
        # Models tab sizer
        models_sizer = wx.BoxSizer(wx.VERTICAL)
        models_sizer.Add(models_splitter, 1, wx.EXPAND)
        self.SetSizer(models_sizer)
    
    def _create_models_list_panel(self) -> None:
        """Create the model list panel for the models tab."""
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Model list header
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        model_label = wx.StaticText(self.models_left_panel, label="Local Models")
        model_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        
        # Refresh button
        self.models_refresh_btn = wx.Button(self.models_left_panel, label="Refresh", size=wx.Size(80, 25))
        self.models_refresh_btn.SetToolTip("Refresh model list from Ollama")
        
        # Add spacer, centered label, and button for proper centering
        header_sizer.AddStretchSpacer(1)
        header_sizer.Add(model_label, 0, wx.ALIGN_CENTER_VERTICAL)
        header_sizer.AddStretchSpacer(1)
        header_sizer.Add(self.models_refresh_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        
        # Model list control (this will be the main model list for the models tab)
        self.models_list = wx.ListCtrl(
            self.models_left_panel,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES
        )
        
        # Add columns - Running column first for visibility
        self.models_list.AppendColumn("Running", width=60)
        self.models_list.AppendColumn("Name", width=200)
        self.models_list.AppendColumn("Size", width=80)
        self.models_list.AppendColumn("Modified", width=100)
        self.models_list.AppendColumn("Capabilities", width=120)
        
        # Add to sizer
        sizer.Add(header_sizer, 0, wx.EXPAND | wx.ALL, 10)
        sizer.Add(self.models_list, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
        self.models_left_panel.SetSizer(sizer)
    
    def _create_models_details_panel(self) -> None:
        """Create the model details and management panel for the models tab."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Top section with management and chat actions side by side
        top_section_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Left column - Model Management
        left_mgmt_sizer = wx.BoxSizer(wx.VERTICAL)
        mgmt_label = wx.StaticText(self.models_right_panel, label="Model Management")
        mgmt_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        
        # Model actions buttons (horizontal layout)
        action_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.models_pull_btn = wx.Button(self.models_right_panel, label="Pull Model", size=wx.Size(100, 30))
        self.models_create_btn = wx.Button(self.models_right_panel, label="Create Model", size=wx.Size(100, 30))
        self.models_delete_btn = wx.Button(self.models_right_panel, label="Delete Model", size=wx.Size(100, 30))
        
        # Initially disable action buttons until a model is selected
        self.models_delete_btn.Enable(False)
        
        action_sizer.Add(self.models_pull_btn, 0, wx.RIGHT, 5)
        action_sizer.Add(self.models_create_btn, 0, wx.RIGHT, 5)
        action_sizer.Add(self.models_delete_btn, 0)
        
        left_mgmt_sizer.Add(mgmt_label, 0, wx.BOTTOM | wx.ALIGN_CENTER_HORIZONTAL, 8)
        left_mgmt_sizer.Add(action_sizer, 0, wx.EXPAND)
        
        # Right column - Chat Actions
        right_chat_sizer = wx.BoxSizer(wx.VERTICAL)
        chat_label = wx.StaticText(self.models_right_panel, label="Chat Actions")
        chat_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        
        chat_action_sizer = wx.BoxSizer(wx.VERTICAL)
        self.models_new_chat_btn = wx.Button(self.models_right_panel, label="New Chat", size=wx.Size(120, 30))
        self.models_new_chat_btn.SetToolTip("Start a new chat with the highlighted model")
        self.models_new_chat_btn.Enable(False)  # Initially disabled until a model is selected
        
        chat_action_sizer.Add(self.models_new_chat_btn, 0, wx.EXPAND)
        
        right_chat_sizer.Add(chat_label, 0, wx.BOTTOM | wx.ALIGN_CENTER_HORIZONTAL, 8)
        right_chat_sizer.Add(chat_action_sizer, 0, wx.EXPAND)
        
        # Add both columns to top section with equal spacing
        top_section_sizer.Add(left_mgmt_sizer, 1, wx.EXPAND | wx.RIGHT, 20)
        top_section_sizer.Add(right_chat_sizer, 1, wx.EXPAND)
        
        # Model details section with tabs (full width)
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
        self.models_details_notebook.AddPage(self.models_modelfile_panel, "Modelfile")
        
        # Add all sections to main sizer
        main_sizer.Add(top_section_sizer, 0, wx.EXPAND | wx.ALL, 15)
        main_sizer.Add(wx.StaticLine(self.models_right_panel), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        main_sizer.Add(info_label, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 15)
        main_sizer.Add(self.models_details_notebook, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)
        
        self.models_right_panel.SetSizer(main_sizer)
    
    def _bind_events(self) -> None:
        """Bind event handlers."""
        # Button events
        self.Bind(wx.EVT_BUTTON, self.on_refresh, self.models_refresh_btn)
        self.Bind(wx.EVT_BUTTON, self.on_pull_model, self.models_pull_btn)
        self.Bind(wx.EVT_BUTTON, self.on_create_model, self.models_create_btn)
        self.Bind(wx.EVT_BUTTON, self.on_delete_model, self.models_delete_btn)
        self.Bind(wx.EVT_BUTTON, self.on_models_new_chat, self.models_new_chat_btn)
        
        # List events
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_model_selected, self.models_list)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_model_double_click, self.models_list)  # Double-click
        self.Bind(wx.EVT_LIST_COL_CLICK, self.on_column_click, self.models_list)
        
        # Notebook events
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_tab_changed, self.models_details_notebook)
    
    def _load_models_async(self) -> None:
        """Load models asynchronously from the cache manager."""
        def load_worker():
            """Worker thread to load models."""
            try:
                models = self.main_window.cache_manager.get_models()
                
                # Update GUI on main thread
                wx.CallAfter(self._on_models_loaded, models)
                
            except Exception as e:
                wx.CallAfter(self._on_models_load_error, e)
        
        # Start loading in background thread
        load_thread = threading.Thread(target=load_worker, daemon=True)
        load_thread.start()
    
    def _on_models_loaded(self, models: List[OllamaModel]) -> None:
        """Handle successful model loading (called on main thread)."""
        self.models = models
        self._sort_models()
        self._update_model_list()
        
        # Auto-select default model if configured
        config = self.main_window.config
        if (config.ui_preferences.auto_select_default_model and 
            config.ui_preferences.default_model and 
            len(self.models) > 0):
            self._select_default_model()
    
    def _on_models_load_error(self, error: Exception) -> None:
        """Handle model loading error (called on main thread)."""
        logger.error(f"Failed to load models: {error}")
        wx.MessageBox(
            f"Failed to load models:\n{str(error)}", 
            "Error Loading Models", 
            wx.OK | wx.ICON_ERROR
        )
    
    def _update_model_list(self) -> None:
        """Update the model list display."""
        self.models_list.DeleteAllItems()
        
        try:
            running_model_names = set(self.main_window.ollama_client.get_running_models())
        except Exception as e:
            logger.warning(f"Could not get running models: {e}")
            running_model_names = set()
        
        for i, model in enumerate(self.models):
            # Running indicator
            running_indicator = "●" if model.name in running_model_names else ""
            
            # Format capabilities
            capabilities_str = ", ".join(model.capabilities) if model.capabilities else "text"
            
            # Insert item
            index = self.models_list.InsertItem(i, running_indicator)
            self.models_list.SetItem(index, 1, model.name)
            self.models_list.SetItem(index, 2, self._format_size(model.size))
            self.models_list.SetItem(index, 3, model.modified_at.strftime('%m/%d %H:%M') if model.modified_at else '')
            self.models_list.SetItem(index, 4, capabilities_str)
        
        # Update status
        self.main_window.status_bar.SetStatusText("Ready", 0)
        self.main_window.status_bar.SetStatusText(f"{len(self.models)} models", 1)
    
    def _format_size(self, size_bytes: int) -> str:
        """Format size in bytes to human readable format."""
        if size_bytes == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0
        size = float(size_bytes)
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        if unit_index == 0:
            return f"{int(size)} {units[unit_index]}"
        else:
            return f"{size:.1f} {units[unit_index]}"
    
    def _select_model_by_name(self, model_name: str) -> None:
        """Select a model by name in the list."""
        try:
            for i in range(self.models_list.GetItemCount()):
                item_name = self.models_list.GetItemText(i, 1)  # Name column
                if item_name == model_name:
                    # Find the model object
                    for model in self.models:
                        if model.name == model_name:
                            # Trigger the selection event manually to update UI
                            self.main_window.current_model = model
                            self.models_delete_btn.Enable(True)
                            self._update_model_details()
                            self.main_window.chat_tab.set_current_model(self.main_window.current_model)
                            self.main_window.chat_tab.start_new_conversation()
                            
                            logger.info(f"Auto-selected created model: {model_name}")
                            break
                    else:
                        logger.warning(f"Could not find created model in list: {model_name}")
        except Exception as e:
            logger.error(f"Error selecting model {model_name}: {e}")
    
    def on_refresh(self, event: wx.CommandEvent) -> None:
        """Handle refresh button - force refresh from server."""
        logger.info("Manual refresh requested - forcing server refresh")
        
        # Disable refresh button to prevent multiple simultaneous refreshes
        self.models_refresh_btn.Enable(False)
        self.main_window.status_bar.SetStatusText("Refreshing models from server...", 0)
        
        def refresh_worker():
            """Worker thread to perform the refresh."""
            try:
                # Update status periodically
                wx.CallAfter(self.main_window.status_bar.SetStatusText, "Fetching model list...", 0)
                
                # Force refresh from server
                models = self.main_window.cache_manager.get_models(force_refresh=True)
                
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
            self.main_window.status_bar.SetStatusText("Error refreshing models", 0)
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
            
            self.main_window.status_bar.SetStatusText("Ready", 0)
            self.main_window.status_bar.SetStatusText(f"{len(self.models)} models", 1)
            
            logger.info("Manual refresh completed successfully")
    
    def on_model_selected(self, event: wx.ListEvent) -> None:
        """Handle model selection (highlighting) - shows details but doesn't change chat model."""
        selection = self.models_list.GetFirstSelected()
        if selection >= 0 and selection < len(self.models):
            # Track highlighted model separately from chat model
            self.highlighted_model = self.models[selection]
            
            # Enable action buttons
            self.models_delete_btn.Enable(True)
            self.models_new_chat_btn.Enable(True)  # Enable new chat button
            
            # Update status bar to show highlighted model
            self.main_window.status_bar.SetStatusText(f"Highlighted: {self.highlighted_model.name}", 1)
            
            # Update model details in the notebook tabs (for highlighted model)
            self._update_highlighted_model_details()
            
            logger.info(f"Highlighted model: {self.highlighted_model.name}")
        else:
            self.highlighted_model = None
            self.models_delete_btn.Enable(False)
            self.models_new_chat_btn.Enable(False)  # Disable new chat button
    
    def on_column_click(self, event: wx.ListEvent) -> None:
        """Handle column header click for sorting."""
        column = event.GetColumn()
        
        # Toggle sort order if clicking the same column
        if column == self.sort_column:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column = column
            self.sort_ascending = True
        
        # Apply sorting
        self._sort_models()
        self._update_model_list()
        
        # Reselect current model if it was selected
        self._reselect_current_model()
        
        logger.debug(f"Sorted by column {column}, ascending: {self.sort_ascending}")
    
    def _sort_models(self) -> None:
        """Sort models based on current sort column and order."""
        def get_sort_key(model: OllamaModel):
            """Get sort key for a model based on current sort column."""
            if self.sort_column == 0:  # Running
                # Get running status
                try:
                    running_model_names = set(self.main_window.ollama_client.get_running_models())
                    return model.name in running_model_names
                except Exception:
                    return False
            elif self.sort_column == 1:  # Name
                return model.name.lower()
            elif self.sort_column == 2:  # Size
                return model.size
            elif self.sort_column == 3:  # Modified
                return model.modified_at or datetime.min
            elif self.sort_column == 4:  # Capabilities
                return ", ".join(sorted(model.capabilities)) if model.capabilities else ""
            else:
                return model.name.lower()
        
        try:
            from datetime import datetime
            self.models.sort(key=get_sort_key, reverse=not self.sort_ascending)
            
            # Save sorting preferences to config if method exists
            config = self.main_window.config
            if hasattr(config, 'ui_preferences') and hasattr(config, 'save_config'):
                config.ui_preferences.model_list_sort_column = self.sort_column
                config.ui_preferences.model_list_sort_ascending = self.sort_ascending
                config.save_config()
            
            logger.debug(f"Sorted {len(self.models)} models by column {self.sort_column}")
            
        except Exception as e:
            logger.error(f"Error sorting models: {e}")
    
    def _reselect_current_model(self) -> None:
        """Reselect the current model in the list after updates."""
        if not self.main_window.current_model:
            return
        
        # Find and select the current model in the updated list
        for i in range(self.models_list.GetItemCount()):
            model_name = self.models_list.GetItemText(i, 1)  # Name column
            if model_name == self.main_window.current_model.name:
                self.models_list.Select(i)
                self.models_list.EnsureVisible(i)
                break
    
    def _update_model_details(self) -> None:
        """Update the model details for the currently selected chat model."""
        if not self.main_window.current_model:
            return
        
        # Update chat tab model
        self.main_window.chat_tab.set_current_model(self.main_window.current_model)
        
        # Reset modelfile loaded flag for new model
        self._modelfile_loaded = False
    
    def _update_highlighted_model_details(self) -> None:
        """Update the model details displayed in the Models tab for the highlighted model."""
        if not self.highlighted_model:
            # Clear model details when no model is highlighted
            self.models_overview_text.SetValue("No model selected.")
            self.models_modelfile_text.SetValue("No model selected.")
            return
            
        # Update Overview tab with basic info for highlighted model
        overview_info = f"Model: {self.highlighted_model.name}\n"
        overview_info += f"Size: {self._format_size(self.highlighted_model.size)}\n"
        overview_info += f"Modified: {self.highlighted_model.modified_at.strftime('%Y-%m-%d %H:%M') if self.highlighted_model.modified_at else 'Unknown'}\n"
        overview_info += f"Digest: {self.highlighted_model.digest[:16] if self.highlighted_model.digest else 'Unknown'}...\n\n"
        
        # Model section (similar to ollama show output)
        overview_info += "Model:\n"
        overview_info += f"  architecture        {self.highlighted_model.details.family or 'Unknown'}\n"
        if self.highlighted_model.details.parameter_size:
            overview_info += f"  parameters          {self.highlighted_model.details.parameter_size}\n"
        
        # Only access model_info if it's already available (don't trigger fetch)
        if hasattr(self.highlighted_model, 'model_info') and self.highlighted_model.model_info:
            info = self.highlighted_model.model_info
            if info.context_length:
                overview_info += f"  context length      {info.context_length}\n"
            if info.embedding_length:
                overview_info += f"  embedding length    {info.embedding_length}\n"
        
        overview_info += f"  quantization        {self.highlighted_model.details.quantization_level or 'Unknown'}\n"
        
        # Add capabilities information to overview
        overview_info += f"\n\nCapabilities:\n"
        if self.highlighted_model.capabilities:
            overview_info += "Detected Capabilities:\n"
            for capability in self.highlighted_model.capabilities:
                overview_info += f"  • {capability.title()}\n"
        else:
            overview_info += "No specific capabilities detected.\n"
        
        # Add capability descriptions
        overview_info += "\nCapability Descriptions:\n"
        if "completion" in self.highlighted_model.capabilities:
            overview_info += "  • Completion: Text generation and conversation\n"
        if "vision" in self.highlighted_model.capabilities:
            overview_info += "  • Vision: Image analysis and description\n"
        if "embedding" in self.highlighted_model.capabilities:
            overview_info += "  • Embedding: Text vectorization for search\n"
        
        self.models_overview_text.SetValue(overview_info)
        
        # Modelfile tab - only load if user switches to it (lazy loading)
        if not self._modelfile_loaded:
            self.models_modelfile_text.SetValue("Click to load modelfile...")
    
    def on_tab_changed(self, event: wx.BookCtrlEvent) -> None:
        """Handle notebook tab change to load modelfile on demand."""
        if event.GetSelection() == 1 and self.highlighted_model and not self._modelfile_loaded:
            # User switched to Modelfile tab - load it
            self._load_modelfile_async()
        
        event.Skip()
    
    def _load_modelfile_async(self) -> None:
        """Load modelfile asynchronously."""
        if not self.highlighted_model:
            return
        
        def load_worker():
            """Worker thread to load modelfile."""
            try:
                modelfile = self.main_window.ollama_client.get_modelfile(self.highlighted_model.name)
                wx.CallAfter(self._on_modelfile_loaded, modelfile)
                
            except Exception as e:
                wx.CallAfter(self._on_modelfile_error, str(e))
        
        # Show loading message
        self.models_modelfile_text.SetValue("Loading modelfile...")
        
        # Start loading in background
        load_thread = threading.Thread(target=load_worker, daemon=True)
        load_thread.start()
    
    def _on_modelfile_loaded(self, modelfile: str) -> None:
        """Handle successful modelfile loading."""
        self.models_modelfile_text.SetValue(modelfile)
        self._modelfile_loaded = True
    
    def _on_modelfile_error(self, error: str) -> None:
        """Handle modelfile loading error."""
        self.models_modelfile_text.SetValue(f"Error loading modelfile:\n{error}")
        logger.error(f"Failed to load modelfile: {error}")
    
    def on_pull_model(self, event: wx.CommandEvent) -> None:
        """Handle pull model button."""
        dialog = wx.TextEntryDialog(
            self, 
            "Enter the model name to pull from Ollama registry:",
            "Pull Model",
            ""
        )
        
        if dialog.ShowModal() == wx.ID_OK:
            model_name = dialog.GetValue().strip()
            if model_name:
                logger.info(f"Starting pull for model: {model_name}")
                # For now, just show a simple message that pull has started
                wx.MessageBox(
                    f"Pull started for model '{model_name}'. Please check the Ollama logs for progress.",
                    "Pull Started",
                    wx.OK | wx.ICON_INFORMATION
                )
                # TODO: Implement proper pull with progress dialog
        
        dialog.Destroy()
    
    def on_create_model(self, event: wx.CommandEvent) -> None:
        """Handle create model button."""
        dialog = CreateModelDialog(self, self.main_window.ollama_client)
        
        if dialog.ShowModal() == wx.ID_OK:
            # Model creation was successful, refresh the list
            created_model_name = dialog.get_created_model_name()
            if created_model_name:
                wx.CallAfter(self._refresh_after_create, created_model_name)
        
        dialog.Destroy()
    
    def _refresh_after_create(self, model_name: str) -> None:
        """Refresh model list after creating a new model."""
        # Refresh the model list
        self._load_models_async()
        
        # Select the newly created model after a brief delay
        if model_name:
            wx.CallLater(1000, self._select_model_by_name, model_name)
    
    def on_delete_model(self, event: wx.CommandEvent) -> None:
        """Handle delete model button."""
        if not self.highlighted_model:
            wx.MessageBox("Please select a model to delete.", "No Model Selected", wx.OK | wx.ICON_WARNING)
            return
        
        # Confirm deletion
        msg = f"Are you sure you want to delete the model '{self.highlighted_model.name}'?\n\nThis action cannot be undone."
        result = wx.MessageBox(msg, "Confirm Model Deletion", wx.YES_NO | wx.ICON_QUESTION)
        
        if result == wx.YES:
            self._delete_model_async(self.highlighted_model.name)
    
    def _delete_model_async(self, model_name: str) -> None:
        """Delete model asynchronously."""
        # Disable delete button during operation
        self.models_delete_btn.Enable(False)
        self.main_window.status_bar.SetStatusText(f"Deleting model {model_name}...", 0)
        
        def delete_worker():
            """Worker thread to delete the model."""
            try:
                success = self.main_window.ollama_client.delete_model(model_name)
                wx.CallAfter(self._on_delete_complete, model_name, success, None)
                
            except Exception as e:
                wx.CallAfter(self._on_delete_complete, model_name, False, str(e))
        
        # Start deletion in background
        delete_thread = threading.Thread(target=delete_worker, daemon=True)
        delete_thread.start()
    
    def _on_delete_complete(self, model_name: str, success: bool, error: Optional[str]) -> None:
        """Handle model deletion completion."""
        # Re-enable delete button
        self.models_delete_btn.Enable(True)
        
        if success:
            self.main_window.status_bar.SetStatusText("Ready", 0)
            logger.info(f"Successfully deleted model: {model_name}")
            
            # Clear current model if it was the deleted one
            if self.main_window.current_model and self.main_window.current_model.name == model_name:
                self.main_window.current_model = None
            
            # Clear highlighted model
            self.highlighted_model = None
            
            # Refresh the model list
            self._load_models_async()
            
        else:
            error_msg = error or "Unknown error occurred"
            self.main_window.status_bar.SetStatusText("Error deleting model", 0)
            logger.error(f"Failed to delete model {model_name}: {error_msg}")
            wx.MessageBox(
                f"Failed to delete model '{model_name}':\n{error_msg}", 
                "Delete Error", 
                wx.OK | wx.ICON_ERROR
            )
    
    def on_models_new_chat(self, event: wx.CommandEvent) -> None:
        """Handle new chat button click from Models tab."""
        try:
            if self.highlighted_model:
                # Set the highlighted model as the current chat model
                self.main_window.current_model = self.highlighted_model
                
                # Save current conversation if it exists and has messages
                self.main_window.chat_tab.save_current_conversation()
                
                # Switch to Chat tab
                self.main_window.notebook.SetSelection(1)  # Chat tab is index 1
                
                # Clear the chat display
                self.main_window.chat_tab.clear_chat()
                
                # Update chat model display
                self.main_window.chat_tab.set_current_model(self.main_window.current_model)
                
                # Start a new conversation with the selected model
                self.main_window.chat_tab.start_new_conversation()
                logger.info(f"Started new chat with {self.highlighted_model.name} from Models tab")
                
                # Update status
                self.main_window.status_bar.SetStatusText(f"New chat started with {self.highlighted_model.name}", 0)
            else:
                wx.MessageBox("Please select a model first.", "No Model Selected", wx.OK | wx.ICON_WARNING)
                
        except Exception as e:
            logger.error(f"Error starting new chat from Models tab: {e}")
    
    def on_model_double_click(self, event: wx.ListEvent) -> None:
        """Handle double-click on model in Models tab."""
        try:
            if self.highlighted_model:
                # Set the highlighted model as the current chat model
                self.main_window.current_model = self.highlighted_model
                
                # Save current conversation if it exists and has messages
                self.main_window.chat_tab.save_current_conversation()
                
                # Switch to Chat tab
                self.main_window.notebook.SetSelection(1)  # Chat tab is index 1
                
                # Clear the chat display
                self.main_window.chat_tab.clear_chat()
                
                # Update chat model display
                self.main_window.chat_tab.set_current_model(self.main_window.current_model)
                
                # Start a new conversation with the selected model
                self.main_window.chat_tab.start_new_conversation()
                logger.info(f"Started new chat with {self.highlighted_model.name} via double-click")
                
                # Update status
                self.main_window.status_bar.SetStatusText(f"New chat started with {self.highlighted_model.name}", 0)
            else:
                wx.MessageBox("Please select a model first.", "No Model Selected", wx.OK | wx.ICON_WARNING)
                
        except Exception as e:
            logger.error(f"Error starting new chat via double-click: {e}")
            wx.MessageBox(f"Error starting new chat: {e}", "Error", wx.OK | wx.ICON_ERROR)
    
    def _select_default_model(self) -> None:
        """Select the configured default model if available."""
        try:
            default_model_name = self.main_window.config.ui_preferences.default_model
            if not default_model_name:
                return
                
            # Find the model in the list
            for i in range(self.models_list.GetItemCount()):
                model_name = self.models_list.GetItemText(i, 1)  # Name column
                if model_name == default_model_name:
                    # Select the item in the list
                    self.models_list.Select(i)
                    self.models_list.EnsureVisible(i)
                    
                    # Find the model object
                    for model in self.models:
                        if model.name == default_model_name:
                            self.main_window.current_model = model
                            self.highlighted_model = model
                            self._update_model_details()
                            self._update_highlighted_model_details()
                            
                            logger.info(f"Auto-selected default model: {default_model_name}")
                            break
                    break
            else:
                logger.warning(f"Default model '{default_model_name}' not found in model list")
                
        except Exception as e:
            logger.error(f"Error selecting default model: {e}")
    
    def get_highlighted_model(self) -> Optional[OllamaModel]:
        """Get the currently highlighted model.
        
        Returns:
            The highlighted model or None if no model is highlighted
        """
        return self.highlighted_model
    
    def refresh_models(self) -> None:
        """Refresh the models list."""
        self._load_models_async()
    
    def get_models(self) -> List[OllamaModel]:
        """Get the current list of models.
        
        Returns:
            List of currently loaded models
        """
        return self.models.copy()
