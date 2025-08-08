"""
Batch image processing panel component.

Allows users to select a vision model, enter a prompt, attach multiple images,
and process them in batch to generate text descriptions saved alongside each image.
"""

import wx
import os
import threading
import asyncio
from typing import List, Optional, Callable
from pathlib import Path

from llamalot.models.chat import ChatImage
from llamalot.models.ollama_model import OllamaModel
from llamalot.backend.ollama_client import OllamaClient
from llamalot.utils.logging_config import get_logger

logger = get_logger(__name__)


class BatchProcessingPanel(wx.Panel):
    """
    Panel for batch processing images with vision models.
    
    Features:
    - Vision model selection dropdown
    - Prompt input text field
    - Image attachment panel
    - Batch processing with progress indication
    - Automatic text file generation next to images
    """
    
    def __init__(self, parent: wx.Window, ollama_client, cache_manager, on_status_update: Optional[Callable[[str], None]] = None):
        """
        Initialize the batch processing panel.
        
        Args:
            parent: Parent window/panel
            ollama_client: OllamaClient instance for API calls
            cache_manager: CacheManager instance for cached model data
            on_status_update: Optional callback for status updates
        """
        super().__init__(parent)
        
        self.ollama_client = ollama_client
        self.cache_manager = cache_manager
        self.on_status_update = on_status_update
        self.vision_models: List[OllamaModel] = []
        self.selected_model: Optional[OllamaModel] = None
        self.attached_images: List[ChatImage] = []
        self.selected_images: List[ChatImage] = []  # Track selected images
        self.image_panels: List[wx.Panel] = []  # Track image panel widgets
        self.is_processing = False
        
        self._create_ui()
        self._bind_events()
        self._load_vision_models()
        
    def _create_ui(self) -> None:
        """Create the user interface."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Title
        title = wx.StaticText(self, label="Batch Image Processing")
        title_font = title.GetFont()
        title_font.PointSize += 2  # Reduced from +4 to +2
        title_font = title_font.Bold()
        title.SetFont(title_font)
        main_sizer.Add(title, 0, wx.ALL | wx.ALIGN_CENTER, 15)  # Increased margin
        
        # Description
        description = wx.StaticText(
            self, 
            label="Select a vision model, enter a prompt, attach images, and process them in batch.\nResults will be saved as text files next to each image."
        )
        description.Wrap(600)
        main_sizer.Add(description, 0, wx.ALL | wx.ALIGN_CENTER, 5)
        
        # Model selection section
        self._create_model_selection(main_sizer)
        
        # Prompt input section
        self._create_prompt_input(main_sizer)
        
        # Image attachment section
        self._create_image_section(main_sizer)
        
        # Processing controls
        self._create_processing_controls(main_sizer)
        
        # Progress section
        self._create_progress_section(main_sizer)
        
        self.SetSizer(main_sizer)
        
    def _create_model_selection(self, parent_sizer: wx.BoxSizer) -> None:
        """Create the model selection section."""
        # Model selection section
        model_label = wx.StaticText(self, label="Vision Model Selection")
        model_font = model_label.GetFont()
        model_font.PointSize += 1
        model_font = model_font.Bold()
        model_label.SetFont(model_font)
        
        model_box = wx.BoxSizer(wx.VERTICAL)
        model_box.Add(model_label, 0, wx.ALL, 2)
        
        # Model dropdown
        model_sizer = wx.BoxSizer(wx.HORIZONTAL)
        model_label = wx.StaticText(self, label="Select Vision Model:")
        self.model_choice = wx.Choice(self, choices=[])
        self.model_choice.SetMinSize(wx.Size(300, -1))
        
        model_sizer.Add(model_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 2)
        model_sizer.Add(self.model_choice, 1, wx.ALL | wx.EXPAND, 2)
        
        # Refresh button
        self.refresh_models_btn = wx.Button(self, label="🔄 Refresh Models", size=wx.Size(120, -1))
        model_sizer.Add(self.refresh_models_btn, 0, wx.ALL, 2)
        
        model_box.Add(model_sizer, 0, wx.ALL | wx.EXPAND, 2)
        parent_sizer.Add(model_box, 0, wx.ALL | wx.EXPAND, 3)
        
    def _create_prompt_input(self, parent_sizer: wx.BoxSizer) -> None:
        """Create the prompt input section."""
        # Prompt and options section
        prompt_label = wx.StaticText(self, label="Prompt & Options")
        prompt_font = prompt_label.GetFont()
        prompt_font.PointSize += 1
        prompt_font = prompt_font.Bold()
        prompt_label.SetFont(prompt_font)
        
        prompt_box = wx.BoxSizer(wx.VERTICAL)
        prompt_box.Add(prompt_label, 0, wx.ALL, 2)
        
        # Prompt input
        prompt_label = wx.StaticText(self, label="Enter prompt to send with each image:")
        self.prompt_text = wx.TextCtrl(
            self, 
            style=wx.TE_MULTILINE,
            size=wx.Size(-1, 100),
            value="Describe this image in detail."
        )
        
        prompt_box.Add(prompt_label, 0, wx.ALL, 2)
        prompt_box.Add(self.prompt_text, 1, wx.ALL | wx.EXPAND, 2)
        
        # Prefix text input
        prefix_label = wx.StaticText(self, label="Text prefix (optional - added before each description):")
        self.prefix_text = wx.TextCtrl(self, size=wx.Size(-1, -1))
        self.prefix_text.SetHint("e.g., 'Image: ' or 'Description: '")
        
        prompt_box.Add(prefix_label, 0, wx.ALL, 2)
        prompt_box.Add(self.prefix_text, 0, wx.ALL | wx.EXPAND, 2)
        
        # File handling options
        options_label = wx.StaticText(self, label="File handling:")
        self.overwrite_radio = wx.RadioButton(self, label="Overwrite existing text files", style=wx.RB_GROUP)
        self.append_radio = wx.RadioButton(self, label="Append to existing text files")
        self.overwrite_radio.SetValue(True)  # Default to overwrite
        
        prompt_box.Add(options_label, 0, wx.ALL, 2)
        prompt_box.Add(self.overwrite_radio, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 2)
        prompt_box.Add(self.append_radio, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 2)  # Reduced bottom margin
        
        parent_sizer.Add(prompt_box, 0, wx.ALL | wx.EXPAND, 3)
        
    def _create_image_section(self, parent_sizer: wx.BoxSizer) -> None:
        """Create the image attachment section with simple layout."""
        # Add minimal spacing to separate from above sections
        parent_sizer.AddSpacer(5)
        
        # Simple title label with clear spacing
        title_label = wx.StaticText(self, label="Images to Process")
        title_font = title_label.GetFont()
        title_font.PointSize += 2  # Make it bigger to be more visible
        title_font = title_font.Bold()
        title_label.SetFont(title_font)
        # Make sure the label can expand and has enough space
        title_label.SetMinSize(wx.Size(200, -1))  # Ensure minimum width
        parent_sizer.Add(title_label, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 3)  # Allow expansion
        
        # Add images button and controls
        controls_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        add_images_btn = wx.Button(self, label="📎 Add Images", size=wx.Size(120, 30))
        add_images_btn.Bind(wx.EVT_BUTTON, self._on_add_images)
        controls_sizer.Add(add_images_btn, 0, wx.ALL, 3)
        
        # Delete selected button
        self.delete_selected_btn = wx.Button(self, label="🗑️ Delete Selected", size=wx.Size(130, 30))
        self.delete_selected_btn.Bind(wx.EVT_BUTTON, self._on_delete_selected)
        self.delete_selected_btn.Enable(False)
        controls_sizer.Add(self.delete_selected_btn, 0, wx.ALL, 3)
        
        # Clear all button
        self.clear_all_btn = wx.Button(self, label="🗑️ Clear All", size=wx.Size(100, 30))
        self.clear_all_btn.Bind(wx.EVT_BUTTON, self._on_clear_all)
        self.clear_all_btn.Enable(False)
        controls_sizer.Add(self.clear_all_btn, 0, wx.ALL, 3)
        
        parent_sizer.Add(controls_sizer, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 3)
        
        # Images display area
        self.images_scroll = wx.ScrolledWindow(self)
        self.images_scroll.SetScrollRate(5, 5)
        self.images_scroll.SetMinSize(wx.Size(400, 150))
        
        self.images_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.images_scroll.SetSizer(self.images_sizer)
        
        # No images label
        self.no_images_label = wx.StaticText(self.images_scroll, label="No images attached. Click 'Add Images' to select files.")
        self.no_images_label.SetForegroundColour(wx.Colour(128, 128, 128))
        self.images_sizer.Add(self.no_images_label, 0, wx.ALL | wx.ALIGN_CENTER, 5)
        
        parent_sizer.Add(self.images_scroll, 1, wx.ALL | wx.EXPAND, 3)
        
    def _create_processing_controls(self, parent_sizer: wx.BoxSizer) -> None:
        """Create the processing control buttons."""
        controls_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.process_btn = wx.Button(self, label="🚀 Start Batch Processing", size=wx.Size(180, 35))
        self.process_btn.SetToolTip("Process all attached images with the selected model and prompt")
        self.process_btn.Enable(False)  # Disabled until ready
        
        self.stop_btn = wx.Button(self, label="⏹️ Stop Processing", size=wx.Size(150, 35))
        self.stop_btn.Enable(False)
        
        controls_sizer.Add(self.process_btn, 0, wx.ALL, 3)
        controls_sizer.Add(self.stop_btn, 0, wx.ALL, 3)
        controls_sizer.AddStretchSpacer()
        
        parent_sizer.Add(controls_sizer, 0, wx.ALL | wx.EXPAND, 3)
        
    def _create_progress_section(self, parent_sizer: wx.BoxSizer) -> None:
        """Create the progress indication section."""
        # Progress section
        progress_label = wx.StaticText(self, label="Progress")
        progress_font = progress_label.GetFont()
        progress_font.PointSize += 1
        progress_font = progress_font.Bold()
        progress_label.SetFont(progress_font)
        # Ensure the progress label has enough space
        progress_label.SetMinSize(wx.Size(100, -1))
        
        progress_box = wx.BoxSizer(wx.VERTICAL)
        progress_box.Add(progress_label, 0, wx.ALL, 2)
        
        # Progress bar
        self.progress_gauge = wx.Gauge(self, range=100)
        
        # Status text
        self.status_text = wx.StaticText(self, label="Ready to process images")
        self.status_text.SetForegroundColour(wx.Colour(0, 100, 0))
        
        # Results summary - constrain height and prevent floating
        results_label = wx.StaticText(self, label="Processing Results (double-click 'Saved to:' lines to open files):")
        self.results_text = wx.TextCtrl(
            self,
            style=wx.TE_MULTILINE | wx.TE_READONLY,
            size=wx.Size(-1, 80)  # Fixed height
        )
        self.results_text.SetMinSize(wx.Size(-1, 80))  # Ensure minimum size
        self.results_text.SetHint("Processing results will appear here. Double-click on a 'Saved to:' line to open the file.")
        
        # Store mapping of result lines to file paths for double-click functionality
        self.result_file_paths: dict[int, str] = {}
        
        progress_box.Add(self.progress_gauge, 0, wx.ALL | wx.EXPAND, 2)
        progress_box.Add(self.status_text, 0, wx.ALL, 2)
        progress_box.Add(results_label, 0, wx.ALL, 2)
        progress_box.Add(self.results_text, 0, wx.ALL | wx.EXPAND, 2)  # Keep at proportion 0 with fixed size
        
        parent_sizer.Add(progress_box, 0, wx.ALL | wx.EXPAND, 3)
        
    def _bind_events(self) -> None:
        """Bind event handlers."""
        self.Bind(wx.EVT_CHOICE, self._on_model_selected, self.model_choice)
        self.Bind(wx.EVT_BUTTON, self._on_refresh_models, self.refresh_models_btn)
        self.Bind(wx.EVT_BUTTON, self._on_start_processing, self.process_btn)
        self.Bind(wx.EVT_BUTTON, self._on_stop_processing, self.stop_btn)
        self.Bind(wx.EVT_TEXT, self._on_prompt_changed, self.prompt_text)
        self.Bind(wx.EVT_LEFT_DCLICK, self._on_results_double_click, self.results_text)
        
    def _load_vision_models(self) -> None:
        """Load available vision models."""
        try:
            # Use cache manager instead of direct ollama client for better performance
            all_models = self.cache_manager.get_models(force_refresh=False)
            self.vision_models = [model for model in all_models if 'vision' in model.capabilities]
            
            # Update choice control
            model_names = [model.name for model in self.vision_models]
            self.model_choice.SetItems(model_names)
            
            if self.vision_models:
                self.model_choice.SetSelection(0)
                self.selected_model = self.vision_models[0]
            
            self._update_process_button_state()
            logger.info(f"Loaded {len(self.vision_models)} vision models for batch processing")
            
        except Exception as e:
            logger.error(f"Error loading vision models: {e}")
            self._update_status(f"Error loading models: {e}", error=True)
            
    def _on_model_selected(self, event: wx.CommandEvent) -> None:
        """Handle model selection change."""
        selection = self.model_choice.GetSelection()
        if selection != wx.NOT_FOUND and selection < len(self.vision_models):
            self.selected_model = self.vision_models[selection]
            self._update_process_button_state()
            logger.info(f"Selected vision model: {self.selected_model.name}")
        
    def _on_refresh_models(self, event: wx.CommandEvent) -> None:
        """Handle refresh models button click."""
        self._load_vision_models()
        self._update_status("Models refreshed")
        
    def _on_prompt_changed(self, event: wx.CommandEvent) -> None:
        """Handle prompt text change."""
        self._update_process_button_state()
        
    def _on_add_images(self, event: wx.CommandEvent) -> None:
        """Handle add images button click."""
        with wx.FileDialog(
            self,
            "Select images to process",
            wildcard="Image files (*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.tiff)|*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.tiff",
            style=wx.FD_OPEN | wx.FD_MULTIPLE
        ) as file_dialog:
            
            if file_dialog.ShowModal() == wx.ID_OK:
                paths = file_dialog.GetPaths()
                
                for path in paths:
                    try:
                        # Create ChatImage from file path
                        chat_image = ChatImage.from_file_path(path)
                        if chat_image and chat_image not in self.attached_images:
                            self.attached_images.append(chat_image)
                            logger.info(f"Added image: {path}")
                    except Exception as e:
                        logger.error(f"Error loading image {path}: {e}")
                        wx.MessageBox(f"Error loading image {path}: {e}", "Error", wx.OK | wx.ICON_ERROR)
                
                self._update_images_display()
                self._update_button_states()
                self._update_process_button_state()
        
    def _update_images_display(self) -> None:
        """Update the images display area."""
        # Clear current display
        self.images_sizer.Clear(delete_windows=True)
        
        if not self.attached_images:
            # Show "no images" message
            self.no_images_label = wx.StaticText(self.images_scroll, label="No images attached. Click 'Add Images' to select files.")
            self.no_images_label.SetForegroundColour(wx.Colour(128, 128, 128))
            self.images_sizer.Add(self.no_images_label, 0, wx.ALL | wx.ALIGN_CENTER, 10)
        else:
            # Show image thumbnails
            for i, image in enumerate(self.attached_images):
                image_panel = self._create_image_thumbnail(image, i)
                self.images_sizer.Add(image_panel, 0, wx.ALL, 5)
        
        self.images_scroll.Layout()
        self.images_scroll.FitInside()
        
    def _create_image_thumbnail(self, image: ChatImage, index: int) -> wx.Panel:
        """Create a thumbnail panel for an image."""
        panel = wx.Panel(self.images_scroll)
        
        # Set background color based on selection state
        if image in self.selected_images:
            panel.SetBackgroundColour(wx.Colour(173, 216, 230))  # Light blue for selected
        else:
            panel.SetBackgroundColour(wx.Colour(245, 245, 245))  # Light gray for unselected
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Thumbnail
        try:
            # Decode base64 image data
            import base64
            import io
            from PIL import Image
            
            image_data = base64.b64decode(image.data)
            pil_image = Image.open(io.BytesIO(image_data))
            
            # Resize image for thumbnail
            pil_image.thumbnail((80, 80))
            
            # Convert to wx.Image
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            wx_img = wx.Image(pil_image.size[0], pil_image.size[1])
            wx_img.SetData(pil_image.tobytes())
            
            # Create bitmap and static bitmap control
            bitmap = wx_img.ConvertToBitmap()
            thumbnail = wx.StaticBitmap(panel, bitmap=bitmap)
            sizer.Add(thumbnail, 0, wx.ALL | wx.ALIGN_CENTER, 2)
            
        except Exception as e:
            # Fallback: show placeholder text
            placeholder = wx.StaticText(panel, label="[Image]")
            sizer.Add(placeholder, 0, wx.ALL | wx.ALIGN_CENTER, 2)
            logger.warning(f"Could not create thumbnail for {image.filename}: {e}")
        
        # Filename
        filename_label = wx.StaticText(panel, label=image.filename or "Unknown")
        filename_label.Wrap(80)
        sizer.Add(filename_label, 0, wx.ALL | wx.ALIGN_CENTER, 2)
        
        # Selection status text
        if image in self.selected_images:
            status_label = wx.StaticText(panel, label="✓ Selected")
            status_label.SetForegroundColour(wx.Colour(0, 100, 0))  # Green
            sizer.Add(status_label, 0, wx.ALL | wx.ALIGN_CENTER, 2)
        else:
            status_label = wx.StaticText(panel, label="Click to select")
            status_label.SetForegroundColour(wx.Colour(100, 100, 100))  # Gray
            sizer.Add(status_label, 0, wx.ALL | wx.ALIGN_CENTER, 2)
        
        # Bind click events to the panel and all its children for selection
        def on_click(evt):
            self._on_image_click(evt, image)
        
        panel.Bind(wx.EVT_LEFT_DOWN, on_click)
        for child in panel.GetChildren():
            child.Bind(wx.EVT_LEFT_DOWN, on_click)
        
        panel.SetSizer(sizer)
        return panel
        
    def _update_process_button_state(self) -> None:
        """Update the process button enabled state."""
        can_process = (
            self.selected_model is not None and
            len(self.attached_images) > 0 and
            len(self.prompt_text.GetValue().strip()) > 0 and
            not self.is_processing
        )
        self.process_btn.Enable(can_process)
        
    def _update_status(self, message: str, error: bool = False) -> None:
        """Update the status display."""
        wx.CallAfter(self._set_status_text, message, error)
        if self.on_status_update:
            self.on_status_update(message)
            
    def _set_status_text(self, message: str, error: bool = False) -> None:
        """Set status text in UI thread."""
        self.status_text.SetLabel(message)
        if error:
            self.status_text.SetForegroundColour(wx.Colour(200, 0, 0))
        else:
            self.status_text.SetForegroundColour(wx.Colour(0, 100, 0))
        self.status_text.GetParent().Layout()
        
    def _on_start_processing(self, event: wx.CommandEvent) -> None:
        """Handle start processing button click."""
        if not self.selected_model or not self.attached_images:
            return
            
        prompt = self.prompt_text.GetValue().strip()
        if not prompt:
            wx.MessageBox("Please enter a prompt", "No Prompt", wx.OK | wx.ICON_WARNING)
            return
            
        # Start processing in background thread
        self.is_processing = True
        self._update_process_button_state()
        self.stop_btn.Enable(True)
        self.progress_gauge.SetValue(0)
        self.results_text.Clear()
        self.result_file_paths.clear()  # Clear file path mappings
        
        # Start processing thread
        processing_thread = threading.Thread(
            target=self._process_images_batch,
            args=(self.selected_model, prompt, self.attached_images.copy()),
            daemon=True
        )
        processing_thread.start()
        
    def _on_stop_processing(self, event: wx.CommandEvent) -> None:
        """Handle stop processing button click."""
        self.is_processing = False
        self.stop_btn.Enable(False)
        self._update_process_button_state()
        self._update_status("Processing stopped by user")
        
    def _on_results_double_click(self, event: wx.MouseEvent) -> None:
        """Handle double-click on results text to open file."""
        try:
            # Get the line that was clicked
            pos = event.GetPosition()
            hit_pos = self.results_text.HitTestPos(pos)
            if hit_pos[0] == wx.TE_HT_UNKNOWN:
                return
                
            text_pos = hit_pos[1]
            line_start = self.results_text.GetLineLength(0)
            
            # Find which line was clicked
            line_num = 0
            current_pos = 0
            text_value = self.results_text.GetValue()
            lines = text_value.split('\n')
            
            for i, line in enumerate(lines):
                if current_pos <= text_pos <= current_pos + len(line):
                    line_num = i
                    break
                current_pos += len(line) + 1  # +1 for newline
            
            # Check if this line contains a file path
            if line_num in self.result_file_paths:
                file_path = self.result_file_paths[line_num]
                if os.path.exists(file_path):
                    # Open the file with the default system application
                    if os.name == 'nt':  # Windows
                        os.startfile(file_path)
                    elif os.name == 'posix':  # Linux/Mac
                        os.system(f'xdg-open "{file_path}"')
                else:
                    wx.MessageBox(f"File not found: {file_path}", "Error", wx.OK | wx.ICON_ERROR)
                    
        except Exception as e:
            logger.error(f"Error opening file: {e}")
        
    def _process_images_batch(self, model: OllamaModel, prompt: str, images: List[ChatImage]) -> None:
        """Process images in batch (runs in background thread)."""
        try:
            total_images = len(images)
            successful = 0
            failed = 0
            
            self._update_status(f"Starting batch processing of {total_images} images...")
            
            for i, image in enumerate(images):
                if not self.is_processing:  # Check for stop signal
                    break
                    
                try:
                    # Update progress
                    progress = int((i / total_images) * 100)
                    wx.CallAfter(self.progress_gauge.SetValue, progress)
                    
                    self._update_status(f"Processing image {i+1}/{total_images}: {image.filename}")
                    
                    # Generate description using Ollama
                    response = self._generate_description(model, prompt, image)
                    
                    # Save to text file
                    self._save_description(image, response)
                    
                    successful += 1
                    
                    # Update results with file path tracking
                    output_file = self._get_output_filename(image)
                    result_msg = f"✅ {image.filename} -> Saved to: {output_file}"
                    self._append_result_with_file_path(result_msg, output_file)
                    
                except Exception as e:
                    failed += 1
                    error_msg = f"❌ {image.filename}: {str(e)}"
                    self._append_result_with_file_path(error_msg, None)
                    logger.error(f"Error processing {image.filename}: {e}")
                    
            # Final update
            wx.CallAfter(self.progress_gauge.SetValue, 100)
            
            if self.is_processing:  # Completed normally
                self._update_status(f"Batch processing completed: {successful} successful, {failed} failed")
            else:  # Stopped by user
                self._update_status(f"Processing stopped: {successful} successful, {failed} failed")
                
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            self._update_status(f"Batch processing error: {e}", error=True)
            
        finally:
            # Reset UI state
            self.is_processing = False
            wx.CallAfter(self._update_process_button_state)
            wx.CallAfter(self.stop_btn.Enable, False)
            
    def _generate_description(self, model: OllamaModel, prompt: str, image: ChatImage) -> str:
        """Generate description for a single image."""
        try:
            # Use the Ollama client to generate a response
            response = self.ollama_client.chat_with_image(
                model_name=model.name,
                prompt=prompt,
                image=image
            )
            return response.strip()
            
        except Exception as e:
            raise Exception(f"Failed to generate description: {e}")
            
    def _save_description(self, image: ChatImage, description: str) -> None:
        """Save description to text file next to the image."""
        try:
            output_path = self._get_output_filename(image)
            
            # Get prefix text if provided
            prefix = self.prefix_text.GetValue().strip()
            if prefix:
                content = f"{prefix}{description}"
            else:
                content = description
            
            # Determine write mode based on user choice
            mode = 'a' if self.append_radio.GetValue() else 'w'
            
            with open(output_path, mode, encoding='utf-8') as f:
                if mode == 'a' and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    # Add a newline before appending if file already has content
                    f.write('\n')
                f.write(content)
                
            action = "Appended to" if mode == 'a' else "Saved description to"
            logger.info(f"{action}: {output_path}")
            
        except Exception as e:
            raise Exception(f"Failed to save description: {e}")
            
    def _get_output_filename(self, image: ChatImage) -> str:
        """Get the output text filename for an image."""
        if image.source_path:
            # Use the original file path, change extension to .txt
            path = Path(image.source_path)
            return str(path.with_suffix('.txt'))
        else:
            # Fallback: save in current directory
            filename = image.filename or "unknown"
            name_without_ext = Path(filename).stem
            return f"{name_without_ext}.txt"
            
    def _append_result_with_file_path(self, message: str, file_path: Optional[str]) -> None:
        """Append a result message and track file path for double-click functionality."""
        def append_text():
            # Get current line count to track which line this will be
            current_text = self.results_text.GetValue()
            line_count = len(current_text.split('\n')) if current_text else 0
            
            # Store file path if provided
            if file_path and "Saved to:" in message:
                self.result_file_paths[line_count] = file_path
            
            # Append the message
            self.results_text.AppendText(message + '\n')
        
        wx.CallAfter(append_text)

    def _on_delete_selected(self, event: wx.CommandEvent) -> None:
        """Handle delete selected images button click."""
        if not self.selected_images:
            return
        
        # Remove selected images from attached_images list
        for selected_image in self.selected_images:
            if selected_image in self.attached_images:
                self.attached_images.remove(selected_image)
        
        # Clear selection
        self.selected_images.clear()
        
        # Refresh the image display
        self._update_images_display()
        self._update_button_states()
        self._update_process_button_state()

    def _on_clear_all(self, event: wx.CommandEvent) -> None:
        """Handle clear all images button click."""
        self.attached_images.clear()
        self.selected_images.clear()
        self._update_images_display()
        self._update_button_states()
        self._update_process_button_state()

    def _on_image_click(self, event: wx.MouseEvent, image: ChatImage) -> None:
        """Handle image click for selection/deselection."""
        if image in self.selected_images:
            # Deselect
            self.selected_images.remove(image)
        else:
            # Select
            self.selected_images.append(image)
        
        # Update visual feedback
        self._update_images_display()
        self._update_button_states()
    
    def _update_button_states(self) -> None:
        """Update the state of delete and clear buttons."""
        has_images = len(self.attached_images) > 0
        has_selected = len(self.selected_images) > 0
        
        self.delete_selected_btn.Enable(has_selected and not self.is_processing)
        self.clear_all_btn.Enable(has_images and not self.is_processing)
