"""
Settings dialog for LlamaLot application.

Provides a comprehensive interface for configuring application settings.
"""

import wx
import wx.lib.scrolledpanel
from typing import List, Optional, Dict, Any
from pathlib import Path

from llamalot.models.config import ApplicationConfig, OllamaServerConfig, UIPreferences, ChatDefaults
from llamalot.utils.logging_config import get_logger

logger = get_logger(__name__)


class SettingsDialog(wx.Dialog):
    """Settings dialog with tabbed interface for configuration."""
    
    def __init__(self, parent: wx.Window, config: ApplicationConfig, available_models: List[str]):
        super().__init__(
            parent,
            title="Settings",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
            size=wx.Size(700, 650)
        )
        
        # Set minimum size to ensure all content is accessible
        self.SetMinSize(wx.Size(650, 600))
        
        self.config = config
        self.available_models = available_models
        self.temp_config = self._copy_config(config)
        
        self._create_ui()
        self._load_values()
        self._setup_bindings()
        
        self.CenterOnParent()
    
    def _copy_config(self, config: ApplicationConfig) -> ApplicationConfig:
        """Create a temporary copy of the configuration for editing."""
        # Create new instances to avoid modifying original
        return ApplicationConfig.from_dict(config.to_dict())
    
    def _create_ui(self) -> None:
        """Create the user interface."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Create notebook for tabs
        self.notebook = wx.Notebook(self)
        
        # Create pages
        self._create_general_page()
        self._create_models_page()
        self._create_server_page()
        self._create_chat_page()
        
        main_sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 10)
        
        # Buttons
        button_sizer = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        main_sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        self.SetSizer(main_sizer)
    
    def _create_general_page(self) -> None:
        """Create the general settings page."""
        panel = wx.Panel(self.notebook)
        self.notebook.AddPage(panel, "General")
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # UI Preferences group
        ui_box = wx.StaticBoxSizer(wx.VERTICAL, panel, "User Interface")
        ui_panel = ui_box.GetStaticBox()
        
        # Theme selection
        theme_sizer = wx.BoxSizer(wx.HORIZONTAL)
        theme_sizer.Add(wx.StaticText(ui_panel, label="Theme:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.theme_choice = wx.Choice(ui_panel, choices=["default", "dark", "light"])
        theme_sizer.Add(self.theme_choice, 1, wx.EXPAND)
        ui_box.Add(theme_sizer, 0, wx.EXPAND | wx.ALL, 8)
        
        # Window size
        size_sizer = wx.FlexGridSizer(2, 2, 8, 15)
        size_sizer.AddGrowableCol(1)
        
        size_sizer.Add(wx.StaticText(ui_panel, label="Window Width:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.window_width_spin = wx.SpinCtrl(ui_panel, min=800, max=2000, initial=1200)
        size_sizer.Add(self.window_width_spin, 1, wx.EXPAND)
        
        size_sizer.Add(wx.StaticText(ui_panel, label="Window Height:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.window_height_spin = wx.SpinCtrl(ui_panel, min=600, max=1500, initial=800)
        size_sizer.Add(self.window_height_spin, 1, wx.EXPAND)
        
        ui_box.Add(size_sizer, 0, wx.EXPAND | wx.ALL, 8)
        
        # Checkboxes with better spacing
        self.window_maximized_cb = wx.CheckBox(ui_panel, label="Start maximized")
        ui_box.Add(self.window_maximized_cb, 0, wx.ALL, 8)
        
        self.show_model_details_cb = wx.CheckBox(ui_panel, label="Show model details panel")
        ui_box.Add(self.show_model_details_cb, 0, wx.ALL, 8)
        
        self.confirm_deletion_cb = wx.CheckBox(ui_panel, label="Confirm model deletion")
        ui_box.Add(self.confirm_deletion_cb, 0, wx.ALL, 8)
        
        sizer.Add(ui_box, 0, wx.EXPAND | wx.ALL, 12)
        
        # Auto-refresh group with improved spacing
        refresh_box = wx.StaticBoxSizer(wx.VERTICAL, panel, "Auto-refresh")
        refresh_panel = refresh_box.GetStaticBox()
        
        self.auto_refresh_cb = wx.CheckBox(refresh_panel, label="Auto-refresh model list")
        refresh_box.Add(self.auto_refresh_cb, 0, wx.ALL, 8)
        
        interval_sizer = wx.BoxSizer(wx.HORIZONTAL)
        interval_sizer.Add(wx.StaticText(refresh_panel, label="Refresh interval (minutes):"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.refresh_interval_spin = wx.SpinCtrl(refresh_panel, min=1, max=60, initial=5)
        interval_sizer.Add(self.refresh_interval_spin, 0)
        refresh_box.Add(interval_sizer, 0, wx.ALL, 8)
        
        sizer.Add(refresh_box, 0, wx.EXPAND | wx.ALL, 12)
        
        panel.SetSizer(sizer)
    
    def _create_models_page(self) -> None:
        """Create the models settings page."""
        panel = wx.Panel(self.notebook)
        self.notebook.AddPage(panel, "Models")
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Default model selection
        default_box = wx.StaticBoxSizer(wx.VERTICAL, panel, "Default Model")
        default_panel = default_box.GetStaticBox()
        
        self.auto_select_cb = wx.CheckBox(default_panel, label="Automatically select default model on startup")
        default_box.Add(self.auto_select_cb, 0, wx.ALL, 8)
        
        model_sizer = wx.BoxSizer(wx.HORIZONTAL)
        model_sizer.Add(wx.StaticText(default_panel, label="Default model:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        
        # Create choice list with "None" option plus available models
        model_choices = ["None"] + self.available_models
        self.default_model_choice = wx.Choice(default_panel, choices=model_choices)
        model_sizer.Add(self.default_model_choice, 1, wx.EXPAND)
        default_box.Add(model_sizer, 0, wx.EXPAND | wx.ALL, 8)
        
        # Help text
        help_text = wx.StaticText(default_panel, 
            label="Select a model to automatically select when the application starts.\n"
                  "Choose 'None' to start with no model selected.")
        help_text.SetFont(help_text.GetFont().Smaller())
        default_box.Add(help_text, 0, wx.ALL, 8)
        
        sizer.Add(default_box, 0, wx.EXPAND | wx.ALL, 12)
        
        # Model list preferences
        list_box = wx.StaticBoxSizer(wx.VERTICAL, panel, "Model List")
        list_panel = list_box.GetStaticBox()
        
        sort_sizer = wx.BoxSizer(wx.HORIZONTAL)
        sort_sizer.Add(wx.StaticText(list_panel, label="Sort by:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.sort_column_choice = wx.Choice(list_panel, choices=["name", "size", "modified", "capabilities"])
        sort_sizer.Add(self.sort_column_choice, 1, wx.EXPAND)
        list_box.Add(sort_sizer, 0, wx.EXPAND | wx.ALL, 8)
        
        self.sort_ascending_cb = wx.CheckBox(list_panel, label="Sort ascending")
        list_box.Add(self.sort_ascending_cb, 0, wx.ALL, 8)
        
        sizer.Add(list_box, 0, wx.EXPAND | wx.ALL, 12)
        
        panel.SetSizer(sizer)
    
    def _create_server_page(self) -> None:
        """Create the server settings page."""
        panel = wx.Panel(self.notebook)
        self.notebook.AddPage(panel, "Server")
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Ollama server configuration
        server_box = wx.StaticBoxSizer(wx.VERTICAL, panel, "Ollama Server Connection")
        server_panel = server_box.GetStaticBox()
        
        # Server connection settings
        grid_sizer = wx.FlexGridSizer(4, 2, 8, 15)
        grid_sizer.AddGrowableCol(1)
        
        grid_sizer.Add(wx.StaticText(server_panel, label="Host:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.host_text = wx.TextCtrl(server_panel)
        grid_sizer.Add(self.host_text, 1, wx.EXPAND)
        
        grid_sizer.Add(wx.StaticText(server_panel, label="Port:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.port_spin = wx.SpinCtrl(server_panel, min=1, max=65535, initial=11434)
        grid_sizer.Add(self.port_spin, 0, wx.EXPAND)
        
        grid_sizer.Add(wx.StaticText(server_panel, label="Timeout (seconds):"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.timeout_spin = wx.SpinCtrl(server_panel, min=5, max=300, initial=30)
        grid_sizer.Add(self.timeout_spin, 0, wx.EXPAND)
        
        server_box.Add(grid_sizer, 0, wx.EXPAND | wx.ALL, 8)
        
        self.use_https_cb = wx.CheckBox(server_panel, label="Use HTTPS")
        server_box.Add(self.use_https_cb, 0, wx.ALL, 8)
        
        # Connection test button
        test_btn = wx.Button(server_panel, label="Test Connection")
        server_box.Add(test_btn, 0, wx.ALL, 8)
        test_btn.Bind(wx.EVT_BUTTON, self._on_test_connection)
        
        sizer.Add(server_box, 0, wx.EXPAND | wx.ALL, 12)
        
        panel.SetSizer(sizer)
    
    def _create_chat_page(self) -> None:
        """Create the chat settings page."""
        # Create a scrolled panel to handle overflow content
        scroll_panel = wx.lib.scrolledpanel.ScrolledPanel(self.notebook)
        scroll_panel.SetupScrolling()
        self.notebook.AddPage(scroll_panel, "Chat")
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Chat defaults
        defaults_box = wx.StaticBoxSizer(wx.VERTICAL, scroll_panel, "Default Chat Parameters")
        defaults_panel = defaults_box.GetStaticBox()
        
        # Parameters grid
        params_grid = wx.FlexGridSizer(5, 2, 8, 15)
        params_grid.AddGrowableCol(1)
        
        params_grid.Add(wx.StaticText(defaults_panel, label="Temperature:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.temperature_text = wx.TextCtrl(defaults_panel)
        params_grid.Add(self.temperature_text, 1, wx.EXPAND)
        
        params_grid.Add(wx.StaticText(defaults_panel, label="Top P:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.top_p_text = wx.TextCtrl(defaults_panel)
        params_grid.Add(self.top_p_text, 1, wx.EXPAND)
        
        params_grid.Add(wx.StaticText(defaults_panel, label="Top K:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.top_k_spin = wx.SpinCtrl(defaults_panel, min=1, max=100, initial=40)
        params_grid.Add(self.top_k_spin, 0, wx.EXPAND)
        
        params_grid.Add(wx.StaticText(defaults_panel, label="Repeat Penalty:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.repeat_penalty_text = wx.TextCtrl(defaults_panel)
        params_grid.Add(self.repeat_penalty_text, 1, wx.EXPAND)
        
        params_grid.Add(wx.StaticText(defaults_panel, label="Context Length:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.context_length_spin = wx.SpinCtrl(defaults_panel, min=512, max=32768, initial=2048)
        params_grid.Add(self.context_length_spin, 0, wx.EXPAND)
        
        defaults_box.Add(params_grid, 0, wx.EXPAND | wx.ALL, 8)
        
        # Other chat settings
        keep_alive_sizer = wx.BoxSizer(wx.HORIZONTAL)
        keep_alive_sizer.Add(wx.StaticText(defaults_panel, label="Keep Alive:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.keep_alive_text = wx.TextCtrl(defaults_panel, value="5m")
        keep_alive_sizer.Add(self.keep_alive_text, 1, wx.EXPAND)
        defaults_box.Add(keep_alive_sizer, 0, wx.EXPAND | wx.ALL, 8)
        
        sizer.Add(defaults_box, 0, wx.EXPAND | wx.ALL, 12)
        
        # Chat UI settings
        ui_box = wx.StaticBoxSizer(wx.VERTICAL, scroll_panel, "Chat Interface")
        ui_panel = ui_box.GetStaticBox()
        
        font_sizer = wx.BoxSizer(wx.HORIZONTAL)
        font_sizer.Add(wx.StaticText(ui_panel, label="Font Size:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.chat_font_size_spin = wx.SpinCtrl(ui_panel, min=8, max=24, initial=12)
        font_sizer.Add(self.chat_font_size_spin, 0)
        ui_box.Add(font_sizer, 0, wx.ALL, 8)
        
        # Font family selection
        font_family_sizer = wx.BoxSizer(wx.HORIZONTAL)
        font_family_sizer.Add(wx.StaticText(ui_panel, label="Font Family:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.chat_font_family_choice = wx.Choice(ui_panel, choices=["Default", "Monospace", "Serif", "Sans-serif"])
        font_family_sizer.Add(self.chat_font_family_choice, 1, wx.EXPAND)
        ui_box.Add(font_family_sizer, 0, wx.EXPAND | wx.ALL, 8)
        
        self.show_timestamps_cb = wx.CheckBox(ui_panel, label="Show timestamps")
        ui_box.Add(self.show_timestamps_cb, 0, wx.ALL, 8)
        
        self.use_ai_titles_cb = wx.CheckBox(ui_panel, label="Use AI-generated conversation titles")
        self.use_ai_titles_cb.SetToolTip("Generate smart titles for conversations using AI (for longer chats)")
        ui_box.Add(self.use_ai_titles_cb, 0, wx.ALL, 8)
        
        self.auto_scroll_chat_cb = wx.CheckBox(ui_panel, label="Auto-scroll chat")
        ui_box.Add(self.auto_scroll_chat_cb, 0, wx.ALL, 8)
        
        self.stream_responses_cb = wx.CheckBox(ui_panel, label="Stream responses")
        ui_box.Add(self.stream_responses_cb, 0, wx.ALL, 8)
        
        sizer.Add(ui_box, 0, wx.EXPAND | wx.ALL, 12)
        
        # Add some extra space at the bottom for scroll comfort
        sizer.Add(wx.Size(0, 20), 0)
        
        scroll_panel.SetSizer(sizer)
    
    def _setup_bindings(self) -> None:
        """Set up event bindings."""
        self.Bind(wx.EVT_BUTTON, self._on_ok, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self._on_cancel, id=wx.ID_CANCEL)
    
    def _load_values(self) -> None:
        """Load current configuration values into the UI."""
        config = self.temp_config
        
        # General page
        self.theme_choice.SetStringSelection(config.ui_preferences.theme)
        self.window_width_spin.SetValue(config.ui_preferences.window_width)
        self.window_height_spin.SetValue(config.ui_preferences.window_height)
        self.window_maximized_cb.SetValue(config.ui_preferences.window_maximized)
        self.show_model_details_cb.SetValue(config.ui_preferences.show_model_details)
        self.confirm_deletion_cb.SetValue(config.ui_preferences.confirm_model_deletion)
        self.auto_refresh_cb.SetValue(config.ui_preferences.auto_refresh_models)
        self.refresh_interval_spin.SetValue(config.ui_preferences.refresh_interval_minutes)
        
        # Models page
        self.auto_select_cb.SetValue(config.ui_preferences.auto_select_default_model)
        if config.ui_preferences.default_model:
            try:
                self.default_model_choice.SetStringSelection(config.ui_preferences.default_model)
            except:
                self.default_model_choice.SetSelection(0)  # "None"
        else:
            self.default_model_choice.SetSelection(0)  # "None"
        
        self.sort_column_choice.SetStringSelection(config.ui_preferences.model_list_sort_column)
        self.sort_ascending_cb.SetValue(config.ui_preferences.model_list_sort_ascending)
        
        # Server page
        self.host_text.SetValue(config.ollama_server.host)
        self.port_spin.SetValue(config.ollama_server.port)
        self.timeout_spin.SetValue(config.ollama_server.timeout)
        self.use_https_cb.SetValue(config.ollama_server.use_https)
        
        # Chat page
        self.temperature_text.SetValue(str(config.chat_defaults.temperature))
        self.top_p_text.SetValue(str(config.chat_defaults.top_p))
        self.top_k_spin.SetValue(config.chat_defaults.top_k)
        self.repeat_penalty_text.SetValue(str(config.chat_defaults.repeat_penalty))
        self.context_length_spin.SetValue(config.chat_defaults.context_length)
        self.keep_alive_text.SetValue(config.chat_defaults.keep_alive or "5m")
        self.chat_font_size_spin.SetValue(config.ui_preferences.chat_font_size)
        self.chat_font_family_choice.SetStringSelection(config.ui_preferences.chat_font_family)
        self.show_timestamps_cb.SetValue(config.ui_preferences.show_timestamps)
        self.use_ai_titles_cb.SetValue(config.ui_preferences.use_ai_generated_titles)
        self.auto_scroll_chat_cb.SetValue(config.ui_preferences.auto_scroll_chat)
        self.stream_responses_cb.SetValue(config.chat_defaults.stream_responses)
    
    def _save_values(self) -> bool:
        """Save UI values to the temporary configuration."""
        try:
            config = self.temp_config
            
            # General page
            config.ui_preferences.theme = self.theme_choice.GetStringSelection()
            config.ui_preferences.window_width = self.window_width_spin.GetValue()
            config.ui_preferences.window_height = self.window_height_spin.GetValue()
            config.ui_preferences.window_maximized = self.window_maximized_cb.GetValue()
            config.ui_preferences.show_model_details = self.show_model_details_cb.GetValue()
            config.ui_preferences.confirm_model_deletion = self.confirm_deletion_cb.GetValue()
            config.ui_preferences.auto_refresh_models = self.auto_refresh_cb.GetValue()
            config.ui_preferences.refresh_interval_minutes = self.refresh_interval_spin.GetValue()
            
            # Models page
            config.ui_preferences.auto_select_default_model = self.auto_select_cb.GetValue()
            selected_model = self.default_model_choice.GetStringSelection()
            config.ui_preferences.default_model = selected_model if selected_model != "None" else None
            
            config.ui_preferences.model_list_sort_column = self.sort_column_choice.GetStringSelection()
            config.ui_preferences.model_list_sort_ascending = self.sort_ascending_cb.GetValue()
            
            # Server page
            config.ollama_server.host = self.host_text.GetValue().strip()
            config.ollama_server.port = self.port_spin.GetValue()
            config.ollama_server.timeout = self.timeout_spin.GetValue()
            config.ollama_server.use_https = self.use_https_cb.GetValue()
            
            # Chat page
            config.chat_defaults.temperature = float(self.temperature_text.GetValue())
            config.chat_defaults.top_p = float(self.top_p_text.GetValue())
            config.chat_defaults.top_k = self.top_k_spin.GetValue()
            config.chat_defaults.repeat_penalty = float(self.repeat_penalty_text.GetValue())
            config.chat_defaults.context_length = self.context_length_spin.GetValue()
            config.chat_defaults.keep_alive = self.keep_alive_text.GetValue().strip()
            config.ui_preferences.chat_font_size = self.chat_font_size_spin.GetValue()
            config.ui_preferences.chat_font_family = self.chat_font_family_choice.GetStringSelection()
            config.ui_preferences.show_timestamps = self.show_timestamps_cb.GetValue()
            config.ui_preferences.use_ai_generated_titles = self.use_ai_titles_cb.GetValue()
            config.ui_preferences.auto_scroll_chat = self.auto_scroll_chat_cb.GetValue()
            config.chat_defaults.stream_responses = self.stream_responses_cb.GetValue()
            
            return True
            
        except ValueError as e:
            wx.MessageBox(f"Invalid value: {e}", "Validation Error", wx.OK | wx.ICON_ERROR)
            return False
        except Exception as e:
            wx.MessageBox(f"Error saving settings: {e}", "Error", wx.OK | wx.ICON_ERROR)
            return False
    
    def _on_test_connection(self, event: wx.CommandEvent) -> None:
        """Test the Ollama server connection."""
        try:
            host = self.host_text.GetValue().strip()
            port = self.port_spin.GetValue()
            use_https = self.use_https_cb.GetValue()
            timeout = self.timeout_spin.GetValue()
            
            protocol = "https" if use_https else "http"
            url = f"{protocol}://{host}:{port}/api/tags"
            
            import requests
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            
            wx.MessageBox("Connection successful!", "Test Connection", wx.OK | wx.ICON_INFORMATION)
            
        except Exception as e:
            wx.MessageBox(f"Connection failed: {e}", "Test Connection", wx.OK | wx.ICON_ERROR)
    
    def _on_ok(self, event: wx.CommandEvent) -> None:
        """Handle OK button click."""
        if self._save_values():
            self.EndModal(wx.ID_OK)
    
    def _on_cancel(self, event: wx.CommandEvent) -> None:
        """Handle Cancel button click."""
        self.EndModal(wx.ID_CANCEL)
    
    def get_config(self) -> ApplicationConfig:
        """Get the modified configuration."""
        return self.temp_config
