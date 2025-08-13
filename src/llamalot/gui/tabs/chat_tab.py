#Chat Tab component for the LlamaLot application.

#- Chat UI with message display and input
#- Conversation management and persistence
#- Image attachments for vision models
#- Real-time message streaming
#- Message formatting and display

import wx
import wx.lib.scrolledpanel
import uuid
import threading
import markdown
import re
from datetime import datetime
from typing import Optional, List
from logging import getLogger

from llamalot.models.chat import ChatConversation, ChatMessage, MessageRole, ChatImage
from llamalot.models.ollama_model import OllamaModel
from llamalot.gui.components.image_attachment_panel import ImageAttachmentPanel

logger = getLogger(__name__)


class ChatTab(wx.lib.scrolledpanel.ScrolledPanel):
    """Chat tab component for conversation with Ollama models."""
    
    def __init__(self, parent: wx.Window, main_window):
        """Initialize the Chat tab.
        
        Args:
            parent: Parent window
            main_window: Reference to the main window for access to managers and status updates
        """
        super().__init__(parent)
        self.SetupScrolling()
        self.main_window = main_window
        
        # Chat state
        self.current_model: Optional[OllamaModel] = None
        self.current_conversation: Optional[ChatConversation] = None
        self.attached_images: List[ChatImage] = []
        self.markdown_enabled: bool = True  # Default to markdown enabled
        
        # Create the UI
        self._create_chat_ui()
        self._bind_events()
        
        logger.info("Chat tab created successfully")
    
    def _create_chat_ui(self) -> None:
        """Create the chat tab UI."""
        # Create header with model display and new chat button
        header_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Top row with Chat title and New Chat button
        title_row_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.current_model_label = wx.StaticText(self, label="Chat")
        self.current_model_label.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        # Ensure the label has enough space for the font
        self.current_model_label.SetMinSize(wx.Size(60, 25))
        
        self.new_chat_btn = wx.Button(self, label="New Chat", size=wx.Size(80, 25))
        self.new_chat_btn.SetToolTip("Start a new conversation with the current model")
        
        # Markdown toggle button
        self.markdown_toggle_btn = wx.Button(self, label="Raw Text", size=wx.Size(80, 25))
        self.markdown_toggle_btn.SetToolTip("Switch to raw text mode")
        
        title_row_sizer.Add(self.current_model_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        title_row_sizer.AddStretchSpacer(1)  # Push the buttons to the right
        title_row_sizer.Add(self.markdown_toggle_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        title_row_sizer.Add(self.new_chat_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        
        # Second row with model information
        self.selected_model_text = wx.StaticText(self, label="No model selected")
        self.selected_model_text.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        
        header_sizer.Add(title_row_sizer, 0, wx.EXPAND | wx.BOTTOM, 8)
        header_sizer.Add(self.selected_model_text, 0, wx.ALIGN_LEFT)
        
        # Chat output display
        self.chat_output = wx.TextCtrl(
            self,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2
        )
        
        # Image attachment panel
        self.image_attachment_panel = ImageAttachmentPanel(
            self,
            on_images_changed=self._on_images_changed
        )
        
        # Chat input controls
        input_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.chat_input = wx.TextCtrl(
            self,
            style=wx.TE_PROCESS_ENTER,
            size=wx.Size(-1, 30)
        )
        self.send_btn = wx.Button(self, label="Send", size=wx.Size(70, 30))
        
        input_sizer.Add(self.chat_input, 1, wx.EXPAND | wx.RIGHT, 5)
        input_sizer.Add(self.send_btn, 0)
        
        # Main layout
        chat_sizer = wx.BoxSizer(wx.VERTICAL)
        chat_sizer.Add(header_sizer, 0, wx.EXPAND | wx.ALL, 10)
        chat_sizer.Add(self.chat_output, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        chat_sizer.Add(self.image_attachment_panel, 0, wx.EXPAND | wx.ALL, 10)
        chat_sizer.Add(input_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        self.SetSizer(chat_sizer)
        
        # Apply initial chat font settings
        self._apply_chat_font_settings()
    
    def _bind_events(self) -> None:
        """Bind event handlers."""
        self.Bind(wx.EVT_BUTTON, self.on_send_message, self.send_btn)
        self.Bind(wx.EVT_BUTTON, self.on_new_chat, self.new_chat_btn)
        self.Bind(wx.EVT_BUTTON, self.on_toggle_markdown, self.markdown_toggle_btn)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_chat_input_enter, self.chat_input)
    
    def _on_images_changed(self, images: List[ChatImage]) -> None:
        """Callback when images are updated in the attachment panel."""
        self.attached_images = images
        logger.info(f"Images updated: {len(images)} images attached")
    
    def set_current_model(self, model: Optional[OllamaModel]) -> None:
        """Set the current model for chat.
        
        Args:
            model: The model to use for chat, or None to clear
        """
        self.current_model = model
        self._update_chat_model_display()
        
        # Update image panel visibility based on model capabilities
        if model and 'vision' in model.capabilities:
            self.image_attachment_panel.show_panel(True)
        else:
            self.image_attachment_panel.show_panel(False)
            self.image_attachment_panel.clear_images()
        
        # Refresh layout
        self.Layout()
        logger.info(f"Current chat model set to: {model.name if model else 'None'}")
    
    def _update_chat_model_display(self) -> None:
        """Update the chat tab to show the currently selected model."""
        if self.current_model:
            model_text = f"Current model: {self.current_model.name}"
            if 'vision' in self.current_model.capabilities:
                model_text += " (Vision)"
        else:
            model_text = "No model selected"
        
        self.selected_model_text.SetLabel(model_text)
    
    def start_new_conversation(self) -> None:
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
    
    def on_new_chat(self, event: wx.CommandEvent) -> None:
        """Handle new chat button click."""
        try:
            # Save current conversation if it exists and has messages
            self.save_current_conversation()
            
            # Clear the chat display
            self.chat_output.SetValue("")
            
            # Start a new conversation with the current model
            if self.current_model:
                self.start_new_conversation()
                logger.info(f"Started new chat with {self.current_model.name}")
                
                # Update status
                self.main_window.status_bar.SetStatusText(f"New chat started with {self.current_model.name}", 0)
            else:
                wx.MessageBox("Please select a model first.", "No Model Selected", wx.OK | wx.ICON_WARNING)
                
        except Exception as e:
            logger.error(f"Error starting new chat: {e}")

    def on_toggle_markdown(self, event: wx.CommandEvent) -> None:
        """Handle markdown toggle button click."""
        try:
            # Toggle markdown state
            self.markdown_enabled = not self.markdown_enabled
            
            # Update button to show what it will switch TO (not current state)
            if self.markdown_enabled:
                # Currently in markdown mode, button should show what we'll switch to
                self.markdown_toggle_btn.SetLabel("Raw Text")
                self.markdown_toggle_btn.SetToolTip("Switch to raw text mode")
            else:
                # Currently in raw text mode, button should show what we'll switch to
                self.markdown_toggle_btn.SetLabel("Markdown")
                self.markdown_toggle_btn.SetToolTip("Switch to markdown rendering mode")
            
            # Re-render the current conversation if it exists
            if self.current_conversation and self.current_conversation.messages:
                self._rerender_conversation()
            
            logger.info(f"Markdown rendering {'enabled' if self.markdown_enabled else 'disabled'}")
            
        except Exception as e:
            logger.error(f"Error toggling markdown: {e}")

    def _rerender_conversation(self) -> None:
        """Re-render the current conversation with the current markdown setting."""
        try:
            if not self.current_conversation or not self.current_conversation.messages:
                return
            
            # Store current scroll position
            current_pos = self.chat_output.GetInsertionPoint()
            
            # Clear the display
            self.chat_output.SetValue("")
            
            # Re-render all messages using original timestamps
            for message in self.current_conversation.messages:
                if message.role == MessageRole.USER:
                    # Use the message's original timestamp, not current time
                    display_message = self._format_message_for_display_with_timestamp(f"> {message.content}", "user", message.images, message.timestamp)
                    self.chat_output.AppendText(display_message)
                elif message.role == MessageRole.ASSISTANT:
                    # For assistant messages, apply markdown formatting if enabled
                    assistant_header = self._format_message_for_display_with_timestamp("🤖 Assistant:", "assistant", None, message.timestamp)
                    self.chat_output.AppendText(assistant_header)
                    
                    # Apply rich text formatting for the content
                    self._apply_rich_text_formatting(message.content, self.chat_output)
                    self.chat_output.AppendText("\n")
            
            # Restore scroll position (approximately)
            try:
                self.chat_output.SetInsertionPoint(min(current_pos, self.chat_output.GetLastPosition()))
            except:
                # If position restore fails, just go to the end
                self.chat_output.SetInsertionPointEnd()
                
        except Exception as e:
            logger.error(f"Error re-rendering conversation: {e}")

    def _apply_markdown_formatting(self, text: str) -> str:
        """Apply markdown formatting to text for display in the rich text control."""
        try:
            if not self.markdown_enabled:
                return text
            
            # For markdown mode, we'll return the original text and apply rich formatting
            # during the display process using wx.TextCtrl rich text methods
            return text
            
        except Exception as e:
            logger.error(f"Error applying markdown formatting: {e}")
            return text

    def _apply_rich_text_formatting(self, text: str, text_ctrl: wx.TextCtrl) -> None:
        """Apply rich text formatting to text using wx.TextCtrl formatting methods."""
        try:
            if not self.markdown_enabled:
                # Plain text mode - just append the text
                text_ctrl.AppendText(text)
                return
            
            # Rich text mode - parse markdown and apply formatting
            self._parse_and_format_markdown(text, text_ctrl)
            
        except Exception as e:
            logger.error(f"Error applying rich text formatting: {e}")
            # Fallback to plain text
            text_ctrl.AppendText(text)

    def _parse_and_format_markdown(self, text: str, text_ctrl: wx.TextCtrl) -> None:
        """Parse markdown text and apply rich formatting to the text control."""
        try:
            # Store current default style
            default_font = text_ctrl.GetFont()
            
            # Process text line by line to handle different markdown elements
            lines = text.split('\n')
            
            for i, line in enumerate(lines):
                self._format_line(line, text_ctrl, default_font)
                
                # Add newline except for the last line
                if i < len(lines) - 1:
                    text_ctrl.AppendText('\n')
                    
        except Exception as e:
            logger.error(f"Error parsing markdown: {e}")
            text_ctrl.AppendText(text)

    def _format_line(self, line: str, text_ctrl: wx.TextCtrl, default_font: wx.Font) -> None:
        """Format a single line of markdown text."""
        try:
            # Handle headers
            if line.startswith('# '):
                # H1 - Large bold
                header_font = wx.Font(default_font.GetPointSize() + 6, default_font.GetFamily(), 
                                    wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
                text_ctrl.SetDefaultStyle(wx.TextAttr(wx.Colour(0, 0, 150), wx.NullColour, header_font))
                text_ctrl.AppendText(line[2:])  # Remove the '# '
                text_ctrl.SetDefaultStyle(wx.TextAttr(wx.NullColour, wx.NullColour, default_font))
                return
            elif line.startswith('## '):
                # H2 - Medium bold
                header_font = wx.Font(default_font.GetPointSize() + 4, default_font.GetFamily(),
                                    wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
                text_ctrl.SetDefaultStyle(wx.TextAttr(wx.Colour(0, 0, 150), wx.NullColour, header_font))
                text_ctrl.AppendText(line[3:])  # Remove the '## '
                text_ctrl.SetDefaultStyle(wx.TextAttr(wx.NullColour, wx.NullColour, default_font))
                return
            elif line.startswith('### '):
                # H3 - Small bold
                header_font = wx.Font(default_font.GetPointSize() + 2, default_font.GetFamily(),
                                    wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
                text_ctrl.SetDefaultStyle(wx.TextAttr(wx.Colour(0, 0, 150), wx.NullColour, header_font))
                text_ctrl.AppendText(line[4:])  # Remove the '### '
                text_ctrl.SetDefaultStyle(wx.TextAttr(wx.NullColour, wx.NullColour, default_font))
                return
            
            # Handle code blocks
            if line.strip().startswith('```'):
                # Code block delimiter - show it styled
                code_font = wx.Font(default_font.GetPointSize(), wx.FONTFAMILY_TELETYPE,
                                  wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
                text_ctrl.SetDefaultStyle(wx.TextAttr(wx.Colour(100, 100, 100), 
                                                    wx.Colour(240, 240, 240), code_font))
                text_ctrl.AppendText(line)
                text_ctrl.SetDefaultStyle(wx.TextAttr(wx.NullColour, wx.NullColour, default_font))
                return
            
            # Handle list items
            if line.strip().startswith('- ') or line.strip().startswith('* '):
                # Bullet list
                text_ctrl.AppendText('• ')
                self._format_inline_text(line.strip()[2:], text_ctrl, default_font)
                return
            elif line.strip() and line.strip()[0].isdigit() and '. ' in line:
                # Numbered list
                parts = line.split('. ', 1)
                if len(parts) == 2:
                    text_ctrl.AppendText(f"{parts[0]}. ")
                    self._format_inline_text(parts[1], text_ctrl, default_font)
                    return
            
            # Handle regular text with inline formatting
            self._format_inline_text(line, text_ctrl, default_font)
            
        except Exception as e:
            logger.error(f"Error formatting line: {e}")
            text_ctrl.AppendText(line)

    def _format_inline_text(self, text: str, text_ctrl: wx.TextCtrl, default_font: wx.Font) -> None:
        """Format inline markdown elements like bold, italic, code."""
        try:
            import re
            
            # Find all markdown patterns
            patterns = [
                (r'\*\*([^*]+)\*\*', 'bold'),      # **bold**
                (r'\*([^*]+)\*', 'italic'),        # *italic*
                (r'`([^`]+)`', 'code'),            # `code`
            ]
            
            # Process text character by character, applying formatting
            pos = 0
            while pos < len(text):
                found_match = False
                
                # Check for markdown patterns at current position
                for pattern, style in patterns:
                    match = re.match(pattern, text[pos:])
                    if match:
                        # Apply the formatting
                        content = match.group(1)
                        
                        if style == 'bold':
                            bold_font = wx.Font(default_font.GetPointSize(), default_font.GetFamily(),
                                              wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
                            text_ctrl.SetDefaultStyle(wx.TextAttr(wx.NullColour, wx.NullColour, bold_font))
                            text_ctrl.AppendText(content)
                        elif style == 'italic':
                            italic_font = wx.Font(default_font.GetPointSize(), default_font.GetFamily(),
                                                wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL)
                            text_ctrl.SetDefaultStyle(wx.TextAttr(wx.NullColour, wx.NullColour, italic_font))
                            text_ctrl.AppendText(content)
                        elif style == 'code':
                            code_font = wx.Font(default_font.GetPointSize(), wx.FONTFAMILY_TELETYPE,
                                              wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
                            text_ctrl.SetDefaultStyle(wx.TextAttr(wx.Colour(150, 0, 150), 
                                                                wx.Colour(250, 250, 250), code_font))
                            text_ctrl.AppendText(content)
                        
                        # Reset to default style
                        text_ctrl.SetDefaultStyle(wx.TextAttr(wx.NullColour, wx.NullColour, default_font))
                        
                        # Move position forward
                        pos += len(match.group(0))
                        found_match = True
                        break
                
                if not found_match:
                    # No markdown pattern found, add the character normally
                    text_ctrl.AppendText(text[pos])
                    pos += 1
                    
        except Exception as e:
            logger.error(f"Error formatting inline text: {e}")
            text_ctrl.AppendText(text)
    
    def _send_chat_message(self) -> None:
        """Send chat message to the current model."""
        message_text = self.chat_input.GetValue().strip()
        if not message_text:
            return
        
        if not self.current_model:
            wx.MessageBox("Please select a model first", "No Model Selected", wx.OK | wx.ICON_WARNING)
            return
            
        if not self.current_conversation:
            self.start_new_conversation()
        
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
        self.main_window.status_bar.SetStatusText("Generating response...", 0)
        
        # Send message asynchronously
        wx.CallAfter(self._send_message_async, message_text, attached_images)
    
    def _send_message_async(self, message: str, attached_images: List[ChatImage]) -> None:
        """Send message to model asynchronously with streaming."""
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
                config = self.main_window.config
                stream_callback = self._stream_callback if config.chat_defaults.stream_responses else None
                
                response_message = self.main_window.ollama_client.chat(
                    model_name=self.current_model.name,
                    conversation=self.current_conversation,
                    stream_callback=stream_callback,
                    temperature=config.chat_defaults.temperature,
                    top_p=config.chat_defaults.top_p,
                    top_k=config.chat_defaults.top_k,
                    repeat_penalty=config.chat_defaults.repeat_penalty,
                    context_length=config.chat_defaults.context_length,
                    keep_alive=config.chat_defaults.keep_alive
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
        # Don't use _format_message_for_display here as it adds timestamps
        # We'll let the full conversation re-rendering handle proper formatting
        assistant_start = "🤖 Assistant:\n"
        self.chat_output.AppendText(assistant_start)
        self._auto_scroll_chat()
        self.main_window.status_bar.SetStatusText("Generating response...", 0)
        
        # Store the position where the response content will start
        self._response_start_pos = self.chat_output.GetLastPosition()

    def _stream_callback(self, chunk: str) -> None:
        """Handle streaming response chunks."""
        # Update UI from main thread
        wx.CallAfter(self._append_response_chunk, chunk)

    def _append_response_chunk(self, chunk: str) -> None:
        """Append a chunk of response to the chat display."""
        if self.markdown_enabled:
            # For streaming with markdown, we'll accumulate chunks and re-render periodically
            # This is less efficient but provides better markdown rendering
            if not hasattr(self, '_current_response_buffer'):
                self._current_response_buffer = ""
            
            self._current_response_buffer += chunk
            
            # Re-render every few chunks or when we hit markdown indicators
            if (len(self._current_response_buffer) % 100 == 0 or 
                any(indicator in chunk for indicator in ['**', '*', '`', '#', '\n'])):
                self._update_streaming_markdown()
        else:
            # Plain text mode - append directly as before
            self.chat_output.AppendText(chunk)
        
        # Auto-scroll if enabled
        self._auto_scroll_chat()

    def _update_streaming_markdown(self) -> None:
        """Update the current streaming response with markdown formatting."""
        try:
            if not hasattr(self, '_current_response_buffer') or not hasattr(self, '_response_start_pos'):
                return
            
            # For now, just show the plain text during streaming
            # We'll apply full markdown formatting at the end
            # This prevents constant re-formatting which can be slow and jumpy
            
            # Replace the content from the response start position with plain text
            self.chat_output.SetSelection(self._response_start_pos, self.chat_output.GetLastPosition())
            self.chat_output.WriteText(self._current_response_buffer)
            
            # Restore insertion point
            self.chat_output.SetInsertionPointEnd()
            
        except Exception as e:
            logger.error(f"Error updating streaming markdown: {e}")
            # Fallback to plain text if markdown fails
            if hasattr(self, '_current_response_buffer'):
                self.chat_output.SetSelection(self._response_start_pos, self.chat_output.GetLastPosition())
                self.chat_output.WriteText(self._current_response_buffer)

    def _finalize_response(self) -> None:
        """Finalize the response and re-enable UI."""
        # Instead of trying to re-format in place, let's just clean up and 
        # re-render the entire conversation for consistency
        if hasattr(self, '_current_response_buffer'):
            delattr(self, '_current_response_buffer')
        if hasattr(self, '_response_start_pos'):
            delattr(self, '_response_start_pos')
        
        # Re-render the entire conversation to ensure consistency with markdown settings
        # This approach is more reliable than trying to patch the streaming response
        if self.current_conversation and self.current_conversation.messages:
            self._rerender_conversation()
        
        self.main_window.status_bar.SetStatusText("Ready", 0)
        self.send_btn.Enable()
        self.chat_input.Enable()
        self.chat_input.SetFocus()
        
        # Refresh model list to update running status since we just chatted with a model
        self.main_window._refresh_model_running_status()
    
    def _handle_send_error(self, error: str) -> None:
        """Handle send error."""
        # Clean up any partial response state
        if hasattr(self, '_current_response_buffer'):
            delattr(self, '_current_response_buffer')
        if hasattr(self, '_response_start_pos'):
            delattr(self, '_response_start_pos')
            
        error_message = self._format_message_for_display(f"Error: {error}", "system")
        self.chat_output.AppendText(error_message)
        self._auto_scroll_chat()
        self.main_window.status_bar.SetStatusText("Error - Ready", 0)
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
                self.main_window.db_manager.save_conversation(self.current_conversation)
                logger.info(f"Saved conversation: {self.current_conversation.title}")
                
                # Refresh chat history if the tab is open
                if hasattr(self.main_window, 'history_tab'):
                    wx.CallAfter(self.main_window.history_tab.refresh_conversation_list)
                
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
            config = self.main_window.config
            if (len(self.current_conversation.messages) >= 4 and  # At least 2 exchanges
                config.ui_preferences.use_ai_generated_titles):  # AI titles enabled
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
            if not self.current_model or not self.main_window.ollama_client or not self.current_conversation:
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
            response = self.main_window.ollama_client.chat(
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
    
    def _apply_chat_font_settings(self) -> None:
        """Apply chat font settings from configuration."""
        try:
            config = self.main_window.config
            if hasattr(config, 'ui_preferences') and hasattr(config.ui_preferences, 'chat_font_size'):
                font_size = config.ui_preferences.chat_font_size
                current_font = self.chat_output.GetFont()
                new_font = wx.Font(
                    font_size,
                    current_font.GetFamily(),
                    current_font.GetStyle(),
                    current_font.GetWeight()
                )
                self.chat_output.SetFont(new_font)
                logger.debug(f"Applied chat font size: {font_size}")
                
        except Exception as e:
            logger.error(f"Error applying chat font settings: {e}")
    
    def _format_message_for_display(self, message: str, role: str, attached_images: Optional[List[ChatImage]] = None) -> str:
        """Format a message for display in the chat output."""
        try:
            formatted_message = ""
            
            # Add timestamp if enabled
            config = self.main_window.config
            if config.ui_preferences.show_timestamps:
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

    def _format_message_for_display_with_timestamp(self, message: str, role: str, attached_images: Optional[List[ChatImage]] = None, message_timestamp: Optional[datetime] = None) -> str:
        """Format a message for display in the chat output with a specific timestamp."""
        try:
            formatted_message = ""
            
            # Add timestamp if enabled and provided
            config = self.main_window.config
            if config.ui_preferences.show_timestamps and message_timestamp:
                timestamp = message_timestamp.strftime("%H:%M:%S")
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
            logger.error(f"Error formatting message for display with timestamp: {e}")
            return f"\n{message}\n"
    
    def _auto_scroll_chat(self) -> None:
        """Auto-scroll chat to bottom if enabled."""
        try:
            config = self.main_window.config
            if config.ui_preferences.auto_scroll_chat and hasattr(self, 'chat_output'):
                self.chat_output.SetInsertionPointEnd()
                
        except Exception as e:
            logger.error(f"Error auto-scrolling chat: {e}")
    
    def clear_chat(self) -> None:
        """Clear the chat display."""
        self.chat_output.SetValue("")
        logger.info("Chat display cleared")
    
    def get_current_conversation(self) -> Optional[ChatConversation]:
        """Get the current conversation.
        
        Returns:
            Current conversation or None if no conversation active
        """
        return self.current_conversation
    
    def set_conversation(self, conversation: Optional[ChatConversation]) -> None:
        """Set the current conversation.
        
        Args:
            conversation: The conversation to set as current, or None to clear
        """
        self.current_conversation = conversation
        logger.info(f"Current conversation set to: {conversation.title if conversation else 'None'}")
