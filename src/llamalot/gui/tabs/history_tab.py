"""
History Tab for LlamaLot GUI.

Provides a conversation history viewer with ability to browse, view, and delete
saved chat conversations.
"""

import wx
import wx.lib.scrolledpanel
import logging
import os
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from llamalot.utils.logging_config import get_logger
from llamalot.models.chat import ChatConversation, MessageRole

if TYPE_CHECKING:
    from llamalot.gui.windows.main_window import MainWindow

logger = get_logger(__name__)


class HistoryTab(wx.lib.scrolledpanel.ScrolledPanel):
    """History tab component for viewing chat conversation history."""
    
    def __init__(self, parent_notebook, db_manager, main_window: Optional['MainWindow'] = None):
        """Initialize the history tab."""
        super().__init__(parent_notebook)
        self.SetupScrolling()
        
        self.notebook = parent_notebook
        self.db_manager = db_manager
        self.main_window = main_window  # Reference to main window for chat operations
        
        # Create the tab content
        self.create_history_tab()
        
    def create_history_tab(self) -> None:
        """Create the chat history tab with conversation list and viewer."""
        # Main splitter for conversation list and detail view
        splitter = wx.SplitterWindow(self, style=wx.SP_3D | wx.SP_LIVE_UPDATE)
        
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
        self.delete_conversation_btn = wx.Button(list_panel, label="Delete Selected")
        self.delete_conversation_btn.SetToolTip("Delete selected conversation")
        self.delete_conversation_btn.Enable(False)
        
        # Reopen chat button
        self.reopen_chat_btn = wx.Button(list_panel, label="Reopen Chat")
        self.reopen_chat_btn.SetToolTip("Reopen selected conversation in chat tab")
        self.reopen_chat_btn.Enable(False)
        
        # Export chat button
        self.export_chat_btn = wx.Button(list_panel, label="Export Chat")
        self.export_chat_btn.SetToolTip("Export selected conversation to file")
        self.export_chat_btn.Enable(False)
        
        # Clear all history button
        self.clear_all_btn = wx.Button(list_panel, label="Clear All History")
        self.clear_all_btn.SetToolTip("Delete all conversation history")
        
        # Button layout - arrange in two rows for better space usage
        button_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # First row: Delete, Reopen, Export
        button_row1 = wx.BoxSizer(wx.HORIZONTAL)
        button_row1.Add(self.delete_conversation_btn, 1, wx.EXPAND | wx.RIGHT, 5)
        button_row1.Add(self.reopen_chat_btn, 1, wx.EXPAND | wx.RIGHT, 5)
        button_row1.Add(self.export_chat_btn, 1, wx.EXPAND)
        
        # Second row: Clear All (centered)
        button_row2 = wx.BoxSizer(wx.HORIZONTAL)
        button_row2.Add(self.clear_all_btn, 0, wx.EXPAND)
        
        button_sizer.Add(button_row1, 0, wx.EXPAND | wx.BOTTOM, 5)
        button_sizer.Add(button_row2, 0, wx.EXPAND)
        
        list_sizer.Add(header_sizer, 0, wx.EXPAND | wx.ALL, 5)
        list_sizer.Add(self.conversation_list, 1, wx.EXPAND | wx.ALL, 5)
        list_sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 5)
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
        self.SetSizer(history_sizer)
        
        # Bind events
        self.refresh_history_btn.Bind(wx.EVT_BUTTON, self.on_refresh_history)
        self.conversation_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_conversation_selected)
        self.conversation_list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.on_conversation_deselected)
        self.delete_conversation_btn.Bind(wx.EVT_BUTTON, self.on_delete_conversation)
        self.reopen_chat_btn.Bind(wx.EVT_BUTTON, self.on_reopen_chat)
        self.export_chat_btn.Bind(wx.EVT_BUTTON, self.on_export_chat)
        self.clear_all_btn.Bind(wx.EVT_BUTTON, self.on_clear_all_history)
        
        # Initialize state
        self.conversation_ids = []
        self.selected_conversation_id = None
        
        # Load initial conversation list
        self.refresh_conversation_list()
    
    def refresh_conversation_list(self) -> None:
        """Refresh the conversation list from the database."""
        try:
            # Clear existing items
            self.conversation_list.DeleteAllItems()
            
            # Get conversations from database - returns tuples of (conversation_id, title, updated_at)
            conversations = self.db_manager.list_conversations(limit=100)
            logger.info(f"Retrieved {len(conversations)} conversations from database")
            
            # Store conversation IDs for lookup
            self.conversation_ids = []
            
            # Populate the list
            for i, (conv_id, title, updated_at) in enumerate(conversations):
                logger.debug(f"Processing conversation {i}: ID={conv_id}, title={title}")
                # Use the actual title from database, or generate a fallback
                display_title = title or f"Conversation {conv_id}"
                index = self.conversation_list.InsertItem(i, display_title)
                
                # Store conversation ID in our lookup list
                self.conversation_ids.append(conv_id)
                logger.debug(f"Added conversation_id to lookup list: {conv_id}")
                
                # Get full conversation to get model name and message count
                full_conv = self.db_manager.get_conversation(conv_id)
                if full_conv:
                    # Display model name, even if the model is no longer available
                    model_display = full_conv.model_name
                    if model_display:
                        # Check if the model still exists in the current model list
                        try:
                            available_models = {model.name for model in self.db_manager.list_models()}
                            if model_display not in available_models:
                                model_display += " (removed)"
                        except Exception:
                            # If we can't check, just show the model name
                            pass
                    else:
                        model_display = "Unknown"
                    
                    self.conversation_list.SetItem(index, 1, model_display)
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
                self.export_chat_btn.Enable(True)
                # Only enable reopen chat if main_window is available
                reopen_enabled = self.main_window is not None
                self.reopen_chat_btn.Enable(reopen_enabled)
                logger.info(f"Conversation selected - Delete enabled: True, Export enabled: True, Reopen enabled: {reopen_enabled}, main_window available: {self.main_window is not None}")
                
                # Force UI refresh
                self.reopen_chat_btn.Refresh()
                self.delete_conversation_btn.Refresh()
                self.export_chat_btn.Refresh()
                
                # Store the current conversation ID for deletion
                self.selected_conversation_id = conv_id
            
        except Exception as e:
            logger.error(f"Error loading conversation: {e}")
            wx.MessageBox(f"Error loading conversation: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def on_conversation_deselected(self, event: wx.ListEvent) -> None:
        """Handle conversation deselection."""
        self.conversation_display.SetValue("")
        self.delete_conversation_btn.Enable(False)
        self.reopen_chat_btn.Enable(False)
        self.export_chat_btn.Enable(False)
        logger.info("Conversation deselected - all buttons disabled")
        
        # Force UI refresh
        self.reopen_chat_btn.Refresh()
        self.delete_conversation_btn.Refresh()
        self.export_chat_btn.Refresh()
        
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
                self.export_chat_btn.Enable(False)
                self.selected_conversation_id = None
                
                logger.info(f"Deleted conversation {conv_id}: {conv_title}")
                
            dlg.Destroy()
            
        except Exception as e:
            logger.error(f"Error deleting conversation: {e}")
            wx.MessageBox(f"Error deleting conversation: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def on_reopen_chat(self, event):
        """Reopen the selected conversation in the chat tab"""
        logger.info(f"Reopen chat button clicked - button enabled: {self.reopen_chat_btn.IsEnabled()}")
        
        # Check if main_window is available
        if not self.main_window:
            wx.MessageBox("Main window reference not available.", "Error", wx.OK | wx.ICON_ERROR)
            return
            
        selected = self.conversation_list.GetFirstSelected()
        logger.info(f"Selected list index: {selected}")
        if selected == -1:
            wx.MessageBox("Please select a conversation to reopen.", "No Selection", wx.OK | wx.ICON_WARNING)
            return
        
        try:
            # Get conversation data - using the same method as selection handler
            if hasattr(self, 'conversation_ids') and 0 <= selected < len(self.conversation_ids):
                conversation_id = self.conversation_ids[selected]
                logger.info(f"Retrieved conversation_id from list: {conversation_id}")
            else:
                # Fallback: try to get from item data
                conversation_id = self.conversation_list.GetItemData(selected)
                logger.info(f"Retrieved conversation_id from item data: {conversation_id}")
                if not conversation_id:
                    logger.error(f"No conversation ID found for selected item {selected}")
                    wx.MessageBox("Could not retrieve conversation ID.", "Error", wx.OK | wx.ICON_ERROR)
                    return
            
            logger.info(f"Attempting to get conversation with ID: {conversation_id}")
            conversation = self.db_manager.get_conversation(conversation_id)
            
            if not conversation:
                logger.error(f"Conversation not found in database: {conversation_id}")
                wx.MessageBox("Conversation not found.", "Error", wx.OK | wx.ICON_ERROR)
                return
            
            logger.info(f"Found conversation: {conversation.title}, model: {conversation.model_name}")
            # The conversation already includes messages, no need to fetch separately
            messages = conversation.messages
            logger.info(f"Conversation has {len(messages)} messages")
            
            # Determine which model to use
            target_model_name = None
            target_model_obj = None
            
            logger.info(f"Determining target model for conversation with model: {conversation.model_name}")
            # First priority: Use the original model if it's available
            if conversation.model_name and conversation.model_name != "Unknown":
                available_models = self.main_window.ollama_client.list_models()
                available_model_dict = {model.name: model for model in available_models}
                logger.info(f"Available models: {list(available_model_dict.keys())}")
                
                if conversation.model_name in available_model_dict:
                    target_model_name = conversation.model_name
                    target_model_obj = available_model_dict[conversation.model_name]
                    logger.info(f"Using original model: {target_model_name}")
                else:
                    logger.info(f"Original model {conversation.model_name} not available, asking user to select")
                    # Ask user if they want to select a different model
                    dlg = wx.MessageDialog(
                        self.main_window,
                        f"The original model '{conversation.model_name}' is no longer available.\n\n"
                        f"Would you like to select a different model to continue this conversation?",
                        "Model Not Available",
                        wx.YES_NO | wx.ICON_QUESTION
                    )
                    
                    result = dlg.ShowModal()
                    dlg.Destroy()
                    
                    if result == wx.ID_YES:
                        # Show model selection dialog
                        model_names = list(available_model_dict.keys())
                        if model_names:
                            dlg = wx.SingleChoiceDialog(
                                self.main_window,
                                "Select a model to continue the conversation:",
                                "Select Model",
                                model_names
                            )
                            
                            if dlg.ShowModal() == wx.ID_OK:
                                target_model_name = dlg.GetStringSelection()
                                target_model_obj = available_model_dict[target_model_name]
                                logger.info(f"User selected model: {target_model_name}")
                            dlg.Destroy()
                        else:
                            wx.MessageBox("No models are available.", "Error", wx.OK | wx.ICON_ERROR)
                            return
                    else:
                        logger.info("User declined to select alternative model")
                        return
            
            # If no model determined yet, use current model or ask user to select
            if not target_model_obj:
                logger.info("No target model determined yet, checking current model")
                # Try to use current model
                if hasattr(self.main_window.chat_tab, 'current_model') and self.main_window.chat_tab.current_model:
                    target_model_obj = self.main_window.chat_tab.current_model
                    target_model_name = target_model_obj.name
                    logger.info(f"Using current chat model: {target_model_name}")
                else:
                    logger.info("No current model, asking user to select")
                    # Ask user to select a model
                    available_models = self.main_window.ollama_client.list_models()
                    available_model_dict = {model.name: model for model in available_models}
                    model_names = list(available_model_dict.keys())
                    
                    if model_names:
                        dlg = wx.SingleChoiceDialog(
                            self.main_window,
                            "Select a model for this conversation:",
                            "Select Model",
                            model_names
                        )
                        
                        if dlg.ShowModal() == wx.ID_OK:
                            target_model_name = dlg.GetStringSelection()
                            target_model_obj = available_model_dict[target_model_name]
                            logger.info(f"User selected model: {target_model_name}")
                        dlg.Destroy()
                    else:
                        wx.MessageBox("No models are available.", "Error", wx.OK | wx.ICON_ERROR)
                        return
            
            if not target_model_obj:
                logger.error("No target model could be determined")
                return
            
            logger.info(f"Final target model: {target_model_name}")
            
            # Switch to chat tab
            logger.info("Switching to chat tab")
            self.main_window.notebook.SetSelection(0)  # Assuming chat tab is at index 0
            
            # Set the model in chat tab
            logger.info(f"Setting model in chat tab: {target_model_name}")
            self.main_window.chat_tab.set_current_model(target_model_obj)
            
            # Load the conversation by setting it directly
            logger.info("Loading conversation into chat tab")
            conversation.messages = messages  # Ensure messages are included
            self.main_window.chat_tab.current_conversation = conversation
            
            # Use the chat tab's proper rendering method instead of manual display
            # This ensures consistency with markdown toggle functionality
            self.main_window.chat_tab._rerender_conversation()
            
            logger.info(f"Successfully reopened conversation with model '{target_model_name}'")
            wx.MessageBox(
                f"Conversation reopened with model '{target_model_name}'.\n\nYou can continue chatting from where you left off.",
                "Success",
                wx.OK | wx.ICON_INFORMATION
            )
            
        except Exception as e:
            logger.error(f"Error reopening conversation: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            wx.MessageBox(f"Error reopening conversation: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)

    def on_export_chat(self, event: wx.CommandEvent) -> None:
        """Handle export chat button click."""
        try:
            if not hasattr(self, 'selected_conversation_id') or not self.selected_conversation_id:
                return
                
            conv_id = self.selected_conversation_id
            selected = self.conversation_list.GetFirstSelected()
            conv_title = self.conversation_list.GetItemText(selected) if selected != -1 else "Unknown"
            
            # Load the conversation
            conversation = self.db_manager.get_conversation(conv_id)
            if not conversation:
                wx.MessageBox("Conversation not found.", "Error", wx.OK | wx.ICON_ERROR)
                return
            
            # Clean up title for filename (remove invalid characters)
            safe_title = "".join(c for c in conv_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            if not safe_title:
                safe_title = f"conversation_{conv_id[:8]}"
            
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
                    
                    # Export the conversation
                    if format_choice == 0:  # Text format
                        self._export_as_text(conversation, filepath)
                    else:  # Markdown format
                        self._export_as_markdown(conversation, filepath)
                    
                    logger.info(f"Exported conversation '{conv_title}' to {filepath}")
                    wx.MessageBox(
                        f"Conversation exported successfully to:\n{filepath}",
                        "Export Complete",
                        wx.OK | wx.ICON_INFORMATION
                    )
                    
        except Exception as e:
            logger.error(f"Error exporting conversation: {e}")
            wx.MessageBox(f"Error exporting conversation: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def _export_as_text(self, conversation: ChatConversation, filepath: str) -> None:
        """Export conversation as plain text."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # Write header
                f.write(f"Conversation: {conversation.title or f'ID {conversation.conversation_id}'}\n")
                f.write(f"Model: {conversation.model_name or 'Unknown'}\n")
                if conversation.created_at:
                    f.write(f"Created: {conversation.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Messages: {len(conversation.messages)}\n")
                f.write("=" * 50 + "\n\n")
                
                # Write messages
                for i, message in enumerate(conversation.messages):
                    if message.role == MessageRole.USER:
                        f.write("User:\n")
                    elif message.role == MessageRole.ASSISTANT:
                        f.write("Assistant:\n")
                    else:
                        f.write(f"[{message.role.value}]:\n")
                    
                    f.write(f"{message.content}\n")
                    
                    # Add spacing between messages
                    if i < len(conversation.messages) - 1:
                        f.write("\n" + "-" * 40 + "\n\n")
                        
        except Exception as e:
            logger.error(f"Error writing text file: {e}")
            raise

    def _export_as_markdown(self, conversation: ChatConversation, filepath: str) -> None:
        """Export conversation as markdown."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # Write header
                f.write(f"# {conversation.title or f'Conversation {conversation.conversation_id}'}\n\n")
                f.write(f"**Model:** {conversation.model_name or 'Unknown'}  \n")
                if conversation.created_at:
                    f.write(f"**Created:** {conversation.created_at.strftime('%Y-%m-%d %H:%M:%S')}  \n")
                f.write(f"**Messages:** {len(conversation.messages)}  \n\n")
                f.write("---\n\n")
                
                # Write messages
                for i, message in enumerate(conversation.messages):
                    if message.role == MessageRole.USER:
                        f.write("## 👤 User\n\n")
                    elif message.role == MessageRole.ASSISTANT:
                        f.write("## 🤖 Assistant\n\n")
                    else:
                        f.write(f"## [{message.role.value}]\n\n")
                    
                    # Write message content with proper markdown formatting
                    content = message.content.strip()
                    f.write(f"{content}\n\n")
                    
                    # Add separator between messages (except for the last one)
                    if i < len(conversation.messages) - 1:
                        f.write("---\n\n")
                        
        except Exception as e:
            logger.error(f"Error writing markdown file: {e}")
            raise

    def on_clear_all_history(self, event):
        """Clear all conversation history"""
        # Confirm deletion
        dlg = wx.MessageDialog(
            self.main_window, 
            "Are you sure you want to delete ALL conversation history?\n\n"
            "This will permanently delete all conversations and messages.\n"
            "This action cannot be undone.",
            "Confirm Clear All History",
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_EXCLAMATION
        )
        
        result = dlg.ShowModal()
        dlg.Destroy()
        
        if result == wx.ID_YES:
            # Double confirmation for this destructive action
            dlg2 = wx.MessageDialog(
                self.main_window,
                "This is your final warning!\n\n"
                "All conversation history will be permanently deleted.\n\n"
                "Are you absolutely sure you want to continue?",
                "Final Confirmation",
                wx.YES_NO | wx.NO_DEFAULT | wx.ICON_STOP
            )
            
            result2 = dlg2.ShowModal()
            dlg2.Destroy()
            
            if result2 == wx.ID_YES:
                try:
                    # Clear all conversations and messages
                    self.db_manager.clear_all_conversations()
                    
                    # Clear viewer
                    self.conversation_display.SetValue("")
                    
                    # Refresh the list
                    self.refresh_conversation_list()
                    
                    wx.MessageBox(
                        "All conversation history has been cleared.",
                        "History Cleared",
                        wx.OK | wx.ICON_INFORMATION
                    )
                    
                except Exception as e:
                    wx.MessageBox(f"Error clearing history: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)

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
