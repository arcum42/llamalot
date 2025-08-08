"""
Create Model Dialog for LlamaLot application.

Provides a dialog for creating new models from Modelfiles.
"""

import wx
import threading
from typing import Optional
from llamalot.utils.logging_config import get_logger

logger = get_logger(__name__)


class CreateModelDialog(wx.Dialog):
    """Dialog for creating new models from Modelfiles."""
    
    def __init__(self, parent, ollama_client, initial_modelfile: str = ""):
        """
        Initialize the Create Model dialog.
        
        Args:
            parent: Parent window
            ollama_client: Ollama client instance for model creation
            initial_modelfile: Initial Modelfile content to populate
        """
        super().__init__(
            parent, 
            title="Create New Model",
            size=wx.Size(800, 600),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        
        self.ollama_client = ollama_client
        self.model_created = False
        self.created_model_name = ""
        
        self._create_ui()
        self._bind_events()
        
        # Populate initial modelfile if provided
        if initial_modelfile:
            processed_modelfile = self._process_modelfile_for_creation(initial_modelfile)
            self.modelfile_text.SetValue(processed_modelfile)
        
        # Center the dialog
        self.CenterOnParent()
        
        logger.info("Create Model dialog initialized")
    
    def _create_ui(self):
        """Create the dialog UI."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Title and description
        title_label = wx.StaticText(self, label="Create New Model")
        title_font = title_label.GetFont()
        title_font.SetPointSize(title_font.GetPointSize() + 2)
        title_font.SetWeight(wx.FONTWEIGHT_BOLD)
        title_label.SetFont(title_font)
        
        desc_label = wx.StaticText(
            self, 
            label="Create a new model by providing a model name and Modelfile content."
        )
        
        main_sizer.Add(title_label, 0, wx.ALL, 10)
        main_sizer.Add(desc_label, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
        # Model name input
        name_panel = wx.Panel(self)
        name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        name_label = wx.StaticText(name_panel, label="Model Name:")
        self.model_name_text = wx.TextCtrl(name_panel, size=wx.Size(300, -1))
        self.model_name_text.SetToolTip("Enter the name for the new model (e.g., 'my-custom-model')")
        
        name_sizer.Add(name_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        name_sizer.Add(self.model_name_text, 1, wx.EXPAND)
        name_panel.SetSizer(name_sizer)
        
        main_sizer.Add(name_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
        # Modelfile editor
        modelfile_label = wx.StaticText(self, label="Modelfile Content:")
        
        self.modelfile_text = wx.TextCtrl(
            self,
            style=wx.TE_MULTILINE | wx.TE_RICH2,
            size=wx.Size(-1, 350)
        )
        self.modelfile_text.SetToolTip("Edit the Modelfile content for your new model")
        
        # Set monospace font for modelfile text
        font = wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.modelfile_text.SetFont(font)
        
        main_sizer.Add(modelfile_label, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        main_sizer.Add(self.modelfile_text, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
        # Progress section (initially hidden)
        self.progress_panel = wx.Panel(self)
        progress_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.progress_label = wx.StaticText(self.progress_panel, label="Creating model...")
        self.progress_gauge = wx.Gauge(self.progress_panel, range=100)
        self.progress_details = wx.StaticText(self.progress_panel, label="")
        
        progress_sizer.Add(self.progress_label, 0, wx.ALL, 5)
        progress_sizer.Add(self.progress_gauge, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        progress_sizer.Add(self.progress_details, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        
        self.progress_panel.SetSizer(progress_sizer)
        self.progress_panel.Hide()
        
        main_sizer.Add(self.progress_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        
        # Buttons
        button_sizer = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        
        # Get the OK button and rename it
        ok_button = self.FindWindow(wx.ID_OK)
        if ok_button:
            ok_button.SetLabel("Create Model")
        
        main_sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        self.SetSizer(main_sizer)
    
    def _bind_events(self):
        """Bind event handlers."""
        self.Bind(wx.EVT_BUTTON, self.on_create_model, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.on_cancel, id=wx.ID_CANCEL)
    
    def _process_modelfile_for_creation(self, modelfile_content: str) -> str:
        """
        Process a modelfile for creating a new model.
        
        Removes the first two comment lines and uncomments the FROM line
        as suggested in the user requirements.
        
        Args:
            modelfile_content: Original modelfile content
            
        Returns:
            Processed modelfile content ready for new model creation
        """
        lines = modelfile_content.split('\n')
        processed_lines = []
        
        skip_first_two_comments = True
        comment_count = 0
        
        for line in lines:
            stripped = line.strip()
            
            # Skip first two comment lines that start with #
            if skip_first_two_comments and stripped.startswith('#'):
                comment_count += 1
                if comment_count <= 2:
                    continue
            
            # Uncomment FROM line if it's commented
            if stripped.startswith('# FROM '):
                processed_lines.append(stripped[2:])  # Remove '# '
                skip_first_two_comments = False
            else:
                processed_lines.append(line)
                if stripped and not stripped.startswith('#'):
                    skip_first_two_comments = False
        
        return '\n'.join(processed_lines)
    
    def on_create_model(self, event):
        """Handle Create Model button click."""
        model_name = self.model_name_text.GetValue().strip()
        modelfile_content = self.modelfile_text.GetValue().strip()
        
        # Validation
        if not model_name:
            wx.MessageBox(
                "Please enter a model name.",
                "Missing Model Name",
                wx.OK | wx.ICON_WARNING
            )
            self.model_name_text.SetFocus()
            return
        
        if not modelfile_content:
            wx.MessageBox(
                "Please enter Modelfile content.",
                "Missing Modelfile Content",
                wx.OK | wx.ICON_WARNING
            )
            self.modelfile_text.SetFocus()
            return
        
        # Validate model name format
        if ':' not in model_name and not model_name.endswith(':latest'):
            # Add :latest tag if no tag specified
            model_name = f"{model_name}:latest"
            self.model_name_text.SetValue(model_name)
        
        # Show progress UI
        self._show_progress(True)
        
        # Disable buttons during creation
        self.FindWindow(wx.ID_OK).Enable(False)
        self.FindWindow(wx.ID_CANCEL).Enable(False)
        
        # Start model creation in background thread
        self.creation_thread = threading.Thread(
            target=self._create_model_thread,
            args=(model_name, modelfile_content),
            daemon=True
        )
        self.creation_thread.start()
    
    def on_cancel(self, event):
        """Handle Cancel button click."""
        self.EndModal(wx.ID_CANCEL)
    
    def _show_progress(self, show: bool):
        """Show or hide the progress panel."""
        if show:
            self.progress_panel.Show()
            self.progress_gauge.Pulse()
        else:
            self.progress_panel.Hide()
            # Stop pulsing if it was active
            self.progress_gauge.SetValue(0)
        
        self.Layout()
    
    def _create_model_thread(self, model_name: str, modelfile_content: str):
        """Create model in background thread."""
        try:
            logger.info(f"Starting model creation: {model_name}")
            
            # Update progress
            wx.CallAfter(self._update_progress, "Initializing model creation...")
            
            # Create the model with progress callback
            success = self.ollama_client.create_model(
                model_name,
                modelfile_content,
                progress_callback=self._on_creation_progress
            )
            
            if success:
                self.model_created = True
                self.created_model_name = model_name
                
                wx.CallAfter(self._on_creation_complete, True, "Model created successfully!")
                logger.info(f"Model creation completed: {model_name}")
            else:
                wx.CallAfter(self._on_creation_complete, False, "Model creation failed")
                logger.error(f"Model creation failed: {model_name}")
        
        except Exception as e:
            error_msg = f"Error creating model: {str(e)}"
            wx.CallAfter(self._on_creation_complete, False, error_msg)
            logger.error(f"Model creation error: {e}")
    
    def _on_creation_progress(self, status: str, data: dict):
        """Handle progress updates from model creation."""
        wx.CallAfter(self._update_progress, status)
    
    def _update_progress(self, status: str):
        """Update progress display."""
        self.progress_details.SetLabel(status)
        self.Layout()
    
    def _on_creation_complete(self, success: bool, message: str):
        """Handle completion of model creation."""
        self._show_progress(False)
        
        # Re-enable buttons
        self.FindWindow(wx.ID_OK).Enable(True)
        self.FindWindow(wx.ID_CANCEL).Enable(True)
        
        if success:
            wx.MessageBox(
                f"Model '{self.created_model_name}' created successfully!",
                "Model Created",
                wx.OK | wx.ICON_INFORMATION
            )
            self.EndModal(wx.ID_OK)
        else:
            wx.MessageBox(
                message,
                "Model Creation Failed",
                wx.OK | wx.ICON_ERROR
            )
    
    def get_created_model_name(self) -> Optional[str]:
        """Get the name of the created model if successful."""
        return self.created_model_name if self.model_created else None
