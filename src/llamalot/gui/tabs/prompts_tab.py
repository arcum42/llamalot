"""
Prompts tab for the LlamaLot application.

Provides functionality to:
- Build custom prompts from base prompts and extra modifiers
- Add, edit, and delete prompts
- Send built prompts to Chat or Batch tabs
- Manage categories and wildcard values
"""

import wx
import wx.lib.scrolledpanel
from typing import Dict, List, Optional, Any
from logging import getLogger

from llamalot.backend.prompts_manager import PromptsManager
from llamalot.models.prompts import BasePrompt, ExtraPrompt

logger = getLogger(__name__)


class PromptEditDialog(wx.Dialog):
    """Dialog for adding/editing prompts."""
    
    def __init__(self, parent, title="Edit Prompt", prompt=None, is_base_prompt=True):
        super().__init__(parent, title=title, size=(600, 500))
        
        self.prompt = prompt
        self.is_base_prompt = is_base_prompt
        
        self._create_ui()
        self._populate_fields()
        
        # Center the dialog
        self.CenterOnParent()
    
    def _create_ui(self):
        """Create the dialog UI."""
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Name field
        name_label = wx.StaticText(panel, label="Name:")
        self.name_ctrl = wx.TextCtrl(panel, size=(400, -1))
        sizer.Add(name_label, 0, wx.ALL, 5)
        sizer.Add(self.name_ctrl, 0, wx.ALL | wx.EXPAND, 5)
        
        # Category field
        category_label = wx.StaticText(panel, label="Category:")
        self.category_ctrl = wx.TextCtrl(panel, size=(400, -1))
        sizer.Add(category_label, 0, wx.ALL, 5)
        sizer.Add(self.category_ctrl, 0, wx.ALL | wx.EXPAND, 5)
        
        # Type field (for extra prompts only)
        if not self.is_base_prompt:
            type_label = wx.StaticText(panel, label="Type:")
            self.type_ctrl = wx.Choice(panel, choices=['boolean', 'wildcard'])
            self.type_ctrl.SetSelection(0)
            sizer.Add(type_label, 0, wx.ALL, 5)
            sizer.Add(self.type_ctrl, 0, wx.ALL | wx.EXPAND, 5)
            
            # Default value (for boolean extra prompts)
            default_label = wx.StaticText(panel, label="Default Value:")
            self.default_ctrl = wx.CheckBox(panel, label="Enabled by default")
            sizer.Add(default_label, 0, wx.ALL, 5)
            sizer.Add(self.default_ctrl, 0, wx.ALL, 5)
        else:
            # Input type field (for base prompts only)
            input_type_label = wx.StaticText(panel, label="Input Type:")
            self.input_type_ctrl = wx.Choice(panel, choices=['text', 'image'])
            self.input_type_ctrl.SetSelection(0)
            sizer.Add(input_type_label, 0, wx.ALL, 5)
            sizer.Add(self.input_type_ctrl, 0, wx.ALL | wx.EXPAND, 5)
        
        # Prompt text field
        prompt_label = wx.StaticText(panel, label="Prompt Text:")
        self.prompt_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE, size=(400, 200))
        sizer.Add(prompt_label, 0, wx.ALL, 5)
        sizer.Add(self.prompt_ctrl, 1, wx.ALL | wx.EXPAND, 5)
        
        # Buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_btn = wx.Button(panel, wx.ID_OK, "OK")
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        button_sizer.Add(ok_btn, 0, wx.ALL, 5)
        button_sizer.Add(cancel_btn, 0, wx.ALL, 5)
        
        sizer.Add(button_sizer, 0, wx.ALL | wx.CENTER, 5)
        
        panel.SetSizer(sizer)
        
        # Bind events
        ok_btn.Bind(wx.EVT_BUTTON, self.on_ok)
    
    def _populate_fields(self):
        """Populate fields if editing existing prompt."""
        if self.prompt:
            self.name_ctrl.SetValue(self.prompt.name)
            self.category_ctrl.SetValue(self.prompt.category)
            self.prompt_ctrl.SetValue(self.prompt.prompt)
            
            if self.is_base_prompt:
                if hasattr(self.prompt, 'input_type'):
                    if self.prompt.input_type == 'image':
                        self.input_type_ctrl.SetSelection(1)
            else:
                # Extra prompt
                if hasattr(self.prompt, 'type'):
                    if self.prompt.type == 'wildcard':
                        self.type_ctrl.SetSelection(1)
                
                if hasattr(self.prompt, 'default') and self.prompt.default:
                    self.default_ctrl.SetValue(True)
    
    def on_ok(self, event):
        """Handle OK button click."""
        # Validate required fields
        if not self.name_ctrl.GetValue().strip():
            wx.MessageBox("Name is required", "Validation Error", wx.OK | wx.ICON_ERROR)
            return
        
        if not self.category_ctrl.GetValue().strip():
            wx.MessageBox("Category is required", "Validation Error", wx.OK | wx.ICON_ERROR)
            return
        
        if not self.prompt_ctrl.GetValue().strip():
            wx.MessageBox("Prompt text is required", "Validation Error", wx.OK | wx.ICON_ERROR)
            return
        
        event.Skip()
    
    def get_prompt_data(self):
        """Get the prompt data from the form."""
        data = {
            'name': self.name_ctrl.GetValue().strip(),
            'category': self.category_ctrl.GetValue().strip(),
            'prompt': self.prompt_ctrl.GetValue().strip()
        }
        
        if self.is_base_prompt:
            data['input_type'] = 'image' if self.input_type_ctrl.GetSelection() == 1 else 'text'
        else:
            data['type'] = 'wildcard' if self.type_ctrl.GetSelection() == 1 else 'boolean'
            data['default'] = self.default_ctrl.GetValue() if hasattr(self, 'default_ctrl') else None
        
        return data


class PromptsTab(wx.lib.scrolledpanel.ScrolledPanel):
    """Prompts tab for building and managing prompt templates."""
    
    def __init__(self, parent: wx.Window, main_window):
        """Initialize the Prompts tab."""
        super().__init__(parent)
        self.SetupScrolling()
        self.main_window = main_window
        
        # Initialize prompts manager
        config_dir = self.main_window.backend_manager.config.data_directory
        self.prompts_manager = PromptsManager(config_dir)
        
        # State
        self.selected_base_prompt = None
        self.selected_extras = {}  # {prompt_id: wildcard_value or True}
        
        # Create UI
        self._create_ui()
        self._bind_events()
        self._refresh_prompts()
        
        logger.info("Prompts tab created successfully")
    
    def _create_ui(self):
        """Create the prompts tab UI."""
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Left panel - Base prompts and extras selection
        left_panel = wx.Panel(self)
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Base prompts section
        base_header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        base_prompts_label = wx.StaticText(left_panel, label="Base Prompts:")
        base_prompts_label.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        base_header_sizer.Add(base_prompts_label, 1, wx.ALL | wx.CENTER, 5)
        
        # Sync from defaults button
        self.sync_defaults_btn = wx.Button(left_panel, label="Sync from Defaults", size=(120, -1))
        base_header_sizer.Add(self.sync_defaults_btn, 0, wx.ALL, 5)
        left_sizer.Add(base_header_sizer, 0, wx.ALL | wx.EXPAND, 5)
        
        # Base prompts list with category filter
        base_filter_sizer = wx.BoxSizer(wx.HORIZONTAL)
        base_filter_sizer.Add(wx.StaticText(left_panel, label="Category:"), 0, wx.ALL | wx.CENTER, 5)
        self.base_category_choice = wx.Choice(left_panel, choices=["All"])
        base_filter_sizer.Add(self.base_category_choice, 1, wx.ALL | wx.EXPAND, 5)
        left_sizer.Add(base_filter_sizer, 0, wx.ALL | wx.EXPAND, 5)
        
        self.base_prompts_list = wx.ListBox(left_panel, size=(300, 150))
        left_sizer.Add(self.base_prompts_list, 0, wx.ALL | wx.EXPAND, 5)
        
        # Base prompts buttons
        base_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.add_base_btn = wx.Button(left_panel, label="Add")
        self.edit_base_btn = wx.Button(left_panel, label="Edit")
        self.delete_base_btn = wx.Button(left_panel, label="Delete")
        base_buttons_sizer.Add(self.add_base_btn, 0, wx.ALL, 2)
        base_buttons_sizer.Add(self.edit_base_btn, 0, wx.ALL, 2)
        base_buttons_sizer.Add(self.delete_base_btn, 0, wx.ALL, 2)
        left_sizer.Add(base_buttons_sizer, 0, wx.ALL | wx.CENTER, 5)
        
        # Extra prompts section
        extra_prompts_label = wx.StaticText(left_panel, label="Extra Prompts:")
        extra_prompts_label.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        left_sizer.Add(extra_prompts_label, 0, wx.ALL, 5)
        
        # Extra prompts list with category filter
        extra_filter_sizer = wx.BoxSizer(wx.HORIZONTAL)
        extra_filter_sizer.Add(wx.StaticText(left_panel, label="Category:"), 0, wx.ALL | wx.CENTER, 5)
        self.extra_category_choice = wx.Choice(left_panel, choices=["All"])
        extra_filter_sizer.Add(self.extra_category_choice, 1, wx.ALL | wx.EXPAND, 5)
        left_sizer.Add(extra_filter_sizer, 0, wx.ALL | wx.EXPAND, 5)
        
        self.extra_prompts_list = wx.CheckListBox(left_panel, size=(300, 200))
        left_sizer.Add(self.extra_prompts_list, 1, wx.ALL | wx.EXPAND, 5)
        
        # Extra prompts buttons
        extra_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.add_extra_btn = wx.Button(left_panel, label="Add")
        self.edit_extra_btn = wx.Button(left_panel, label="Edit")
        self.delete_extra_btn = wx.Button(left_panel, label="Delete")
        extra_buttons_sizer.Add(self.add_extra_btn, 0, wx.ALL, 2)
        extra_buttons_sizer.Add(self.edit_extra_btn, 0, wx.ALL, 2)
        extra_buttons_sizer.Add(self.delete_extra_btn, 0, wx.ALL, 2)
        left_sizer.Add(extra_buttons_sizer, 0, wx.ALL | wx.CENTER, 5)
        
        left_panel.SetSizer(left_sizer)
        
        # Right panel - Prompt building and output
        right_panel = wx.Panel(self)
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Built prompt display
        built_prompt_label = wx.StaticText(right_panel, label="Built Prompt:")
        built_prompt_label.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        right_sizer.Add(built_prompt_label, 0, wx.ALL, 5)
        
        self.built_prompt_text = wx.TextCtrl(right_panel, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(400, 300))
        right_sizer.Add(self.built_prompt_text, 1, wx.ALL | wx.EXPAND, 5)
        
        # Wildcard values section
        wildcard_label = wx.StaticText(right_panel, label="Wildcard Values:")
        wildcard_label.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        right_sizer.Add(wildcard_label, 0, wx.ALL, 5)
        
        # Scrollable panel for wildcard inputs
        self.wildcard_panel = wx.lib.scrolledpanel.ScrolledPanel(right_panel, size=(400, 100))
        self.wildcard_panel.SetupScrolling()
        self.wildcard_sizer = wx.BoxSizer(wx.VERTICAL)
        self.wildcard_panel.SetSizer(self.wildcard_sizer)
        right_sizer.Add(self.wildcard_panel, 0, wx.ALL | wx.EXPAND, 5)
        
        # Action buttons
        action_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.send_to_chat_btn = wx.Button(right_panel, label="Send to New Chat")
        self.send_to_batch_btn = wx.Button(right_panel, label="Send to Batch")
        self.copy_prompt_btn = wx.Button(right_panel, label="Copy to Clipboard")
        action_buttons_sizer.Add(self.send_to_chat_btn, 0, wx.ALL, 5)
        action_buttons_sizer.Add(self.send_to_batch_btn, 0, wx.ALL, 5)
        action_buttons_sizer.Add(self.copy_prompt_btn, 0, wx.ALL, 5)
        right_sizer.Add(action_buttons_sizer, 0, wx.ALL | wx.CENTER, 5)
        
        right_panel.SetSizer(right_sizer)
        
        # Add panels to main sizer
        main_sizer.Add(left_panel, 1, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(right_panel, 1, wx.ALL | wx.EXPAND, 5)
        
        self.SetSizer(main_sizer)
    
    def _bind_events(self):
        """Bind UI events."""
        # Sync button
        self.sync_defaults_btn.Bind(wx.EVT_BUTTON, self.on_sync_defaults)
        
        # Base prompts events
        self.base_category_choice.Bind(wx.EVT_CHOICE, self.on_base_category_changed)
        self.base_prompts_list.Bind(wx.EVT_LISTBOX, self.on_base_prompt_selected)
        self.add_base_btn.Bind(wx.EVT_BUTTON, self.on_add_base_prompt)
        self.edit_base_btn.Bind(wx.EVT_BUTTON, self.on_edit_base_prompt)
        self.delete_base_btn.Bind(wx.EVT_BUTTON, self.on_delete_base_prompt)
        
        # Extra prompts events
        self.extra_category_choice.Bind(wx.EVT_CHOICE, self.on_extra_category_changed)
        self.extra_prompts_list.Bind(wx.EVT_CHECKLISTBOX, self.on_extra_prompt_checked)
        self.add_extra_btn.Bind(wx.EVT_BUTTON, self.on_add_extra_prompt)
        self.edit_extra_btn.Bind(wx.EVT_BUTTON, self.on_edit_extra_prompt)
        self.delete_extra_btn.Bind(wx.EVT_BUTTON, self.on_delete_extra_prompt)
        
        # Action buttons
        self.send_to_chat_btn.Bind(wx.EVT_BUTTON, self.on_send_to_chat)
        self.send_to_batch_btn.Bind(wx.EVT_BUTTON, self.on_send_to_batch)
        self.copy_prompt_btn.Bind(wx.EVT_BUTTON, self.on_copy_prompt)
    
    def _refresh_prompts(self):
        """Refresh the prompts lists and categories."""
        # Update categories
        categories = ["All"] + self.prompts_manager.get_categories()
        
        self.base_category_choice.SetItems(categories)
        self.base_category_choice.SetSelection(0)
        
        self.extra_category_choice.SetItems(categories)
        self.extra_category_choice.SetSelection(0)
        
        # Update lists
        self._update_base_prompts_list()
        self._update_extra_prompts_list()
        
        # Update built prompt
        self._update_built_prompt()
    
    def _update_base_prompts_list(self):
        """Update the base prompts list based on selected category."""
        category = self.base_category_choice.GetStringSelection()
        
        if category == "All":
            prompts = list(self.prompts_manager.get_base_prompts().values())
        else:
            prompts = self.prompts_manager.get_base_prompts_by_category(category)
        
        # Sort by name
        prompts.sort(key=lambda p: p.name)
        
        # Update list
        self.base_prompts_list.Clear()
        for prompt in prompts:
            self.base_prompts_list.Append(prompt.name, prompt)
    
    def _update_extra_prompts_list(self):
        """Update the extra prompts list based on selected category."""
        category = self.extra_category_choice.GetStringSelection()
        
        if category == "All":
            prompts = list(self.prompts_manager.get_extra_prompts().values())
        else:
            prompts = self.prompts_manager.get_extra_prompts_by_category(category)
        
        # Sort by name
        prompts.sort(key=lambda p: p.name)
        
        # Update list
        self.extra_prompts_list.Clear()
        for prompt in prompts:
            index = self.extra_prompts_list.Append(prompt.name)
            self.extra_prompts_list.SetClientData(index, prompt)
            
            # Set default checked state
            if prompt.default and prompt.id not in self.selected_extras:
                self.extra_prompts_list.Check(index, True)
                self.selected_extras[prompt.id] = True
    
    def _update_wildcard_inputs(self):
        """Update wildcard input fields based on selected extra prompts."""
        # Clear existing inputs
        self.wildcard_sizer.Clear(True)
        
        # Add inputs for wildcard prompts
        for i in range(self.extra_prompts_list.GetCount()):
            if self.extra_prompts_list.IsChecked(i):
                prompt = self.extra_prompts_list.GetClientData(i)
                if prompt and prompt.type == 'wildcard':
                    # Create input for this wildcard
                    label = wx.StaticText(self.wildcard_panel, label=f"{prompt.name}:")
                    text_ctrl = wx.TextCtrl(self.wildcard_panel, size=(300, -1))
                    text_ctrl.prompt_id = prompt.id
                    text_ctrl.Bind(wx.EVT_TEXT, self.on_wildcard_changed)
                    
                    # Set existing value if any
                    if prompt.id in self.selected_extras and isinstance(self.selected_extras[prompt.id], str):
                        text_ctrl.SetValue(self.selected_extras[prompt.id])
                    
                    self.wildcard_sizer.Add(label, 0, wx.ALL, 2)
                    self.wildcard_sizer.Add(text_ctrl, 0, wx.ALL | wx.EXPAND, 2)
        
        self.wildcard_panel.SetupScrolling()
        self.wildcard_panel.Layout()
        self.Layout()
    
    def _update_built_prompt(self):
        """Update the built prompt display."""
        if self.selected_base_prompt:
            # Get wildcard values
            wildcard_values = {}
            for prompt_id, value in self.selected_extras.items():
                if isinstance(value, str):
                    wildcard_values[prompt_id] = value
            
            # Get selected extra prompt IDs
            selected_extra_ids = [
                prompt_id for prompt_id, value in self.selected_extras.items()
                if value  # True for boolean, non-empty string for wildcard
            ]
            
            # Build the prompt
            built_prompt = self.prompts_manager.build_final_prompt(
                self.selected_base_prompt.id,
                selected_extra_ids,
                wildcard_values
            )
            
            self.built_prompt_text.SetValue(built_prompt)
        else:
            self.built_prompt_text.SetValue("")
    
    # Event handlers
    def on_base_category_changed(self, event):
        """Handle base category selection change."""
        self._update_base_prompts_list()
    
    def on_base_prompt_selected(self, event):
        """Handle base prompt selection."""
        selection = self.base_prompts_list.GetSelection()
        if selection != wx.NOT_FOUND:
            self.selected_base_prompt = self.base_prompts_list.GetClientData(selection)
            self._update_built_prompt()
    
    def on_extra_category_changed(self, event):
        """Handle extra category selection change."""
        self._update_extra_prompts_list()
        self._update_wildcard_inputs()
        self._update_built_prompt()
    
    def on_extra_prompt_checked(self, event):
        """Handle extra prompt checked/unchecked."""
        index = event.GetSelection()
        prompt = self.extra_prompts_list.GetClientData(index)
        
        if self.extra_prompts_list.IsChecked(index):
            self.selected_extras[prompt.id] = True
        else:
            if prompt.id in self.selected_extras:
                del self.selected_extras[prompt.id]
        
        self._update_wildcard_inputs()
        self._update_built_prompt()
    
    def on_wildcard_changed(self, event):
        """Handle wildcard value change."""
        text_ctrl = event.GetEventObject()
        if hasattr(text_ctrl, 'prompt_id'):
            value = text_ctrl.GetValue().strip()
            if value:
                self.selected_extras[text_ctrl.prompt_id] = value
            else:
                self.selected_extras[text_ctrl.prompt_id] = True  # Keep checked but no value
            
            self._update_built_prompt()
    
    def on_add_base_prompt(self, event):
        """Handle add base prompt."""
        dialog = PromptEditDialog(self, "Add Base Prompt", is_base_prompt=True)
        if dialog.ShowModal() == wx.ID_OK:
            data = dialog.get_prompt_data()
            if self.prompts_manager.add_base_prompt(
                data['name'], data['category'], data['input_type'], data['prompt']
            ):
                self._refresh_prompts()
            else:
                wx.MessageBox("Failed to add base prompt", "Error", wx.OK | wx.ICON_ERROR)
        dialog.Destroy()
    
    def on_edit_base_prompt(self, event):
        """Handle edit base prompt."""
        selection = self.base_prompts_list.GetSelection()
        if selection == wx.NOT_FOUND:
            wx.MessageBox("Please select a base prompt to edit", "No Selection", wx.OK | wx.ICON_WARNING)
            return
        
        prompt = self.base_prompts_list.GetClientData(selection)
        dialog = PromptEditDialog(self, "Edit Base Prompt", prompt, is_base_prompt=True)
        if dialog.ShowModal() == wx.ID_OK:
            data = dialog.get_prompt_data()
            if self.prompts_manager.update_base_prompt(
                prompt.id, data['name'], data['category'], data['input_type'], data['prompt']
            ):
                self._refresh_prompts()
            else:
                wx.MessageBox("Failed to update base prompt", "Error", wx.OK | wx.ICON_ERROR)
        dialog.Destroy()
    
    def on_delete_base_prompt(self, event):
        """Handle delete base prompt."""
        selection = self.base_prompts_list.GetSelection()
        if selection == wx.NOT_FOUND:
            wx.MessageBox("Please select a base prompt to delete", "No Selection", wx.OK | wx.ICON_WARNING)
            return
        
        prompt = self.base_prompts_list.GetClientData(selection)
        if wx.MessageBox(
            f"Are you sure you want to delete the base prompt '{prompt.name}'?",
            "Confirm Delete", wx.YES_NO | wx.ICON_QUESTION
        ) == wx.YES:
            if self.prompts_manager.remove_base_prompt(prompt.id):
                if self.selected_base_prompt and self.selected_base_prompt.id == prompt.id:
                    self.selected_base_prompt = None
                self._refresh_prompts()
            else:
                wx.MessageBox("Failed to delete base prompt", "Error", wx.OK | wx.ICON_ERROR)
    
    def on_add_extra_prompt(self, event):
        """Handle add extra prompt."""
        dialog = PromptEditDialog(self, "Add Extra Prompt", is_base_prompt=False)
        if dialog.ShowModal() == wx.ID_OK:
            data = dialog.get_prompt_data()
            if self.prompts_manager.add_extra_prompt(
                data['name'], data['category'], data['type'], data['prompt'], data.get('default')
            ):
                self._refresh_prompts()
            else:
                wx.MessageBox("Failed to add extra prompt", "Error", wx.OK | wx.ICON_ERROR)
        dialog.Destroy()
    
    def on_edit_extra_prompt(self, event):
        """Handle edit extra prompt."""
        selections = self.extra_prompts_list.GetSelections()
        if not selections:
            wx.MessageBox("Please select an extra prompt to edit", "No Selection", wx.OK | wx.ICON_WARNING)
            return
        
        selection = selections[0]
        prompt = self.extra_prompts_list.GetClientData(selection)
        dialog = PromptEditDialog(self, "Edit Extra Prompt", prompt, is_base_prompt=False)
        if dialog.ShowModal() == wx.ID_OK:
            data = dialog.get_prompt_data()
            if self.prompts_manager.update_extra_prompt(
                prompt.id, data['name'], data['category'], data['type'], data['prompt'], data.get('default')
            ):
                self._refresh_prompts()
            else:
                wx.MessageBox("Failed to update extra prompt", "Error", wx.OK | wx.ICON_ERROR)
        dialog.Destroy()
    
    def on_delete_extra_prompt(self, event):
        """Handle delete extra prompt."""
        selections = self.extra_prompts_list.GetSelections()
        if not selections:
            wx.MessageBox("Please select an extra prompt to delete", "No Selection", wx.OK | wx.ICON_WARNING)
            return
        
        selection = selections[0]
        prompt = self.extra_prompts_list.GetClientData(selection)
        if wx.MessageBox(
            f"Are you sure you want to delete the extra prompt '{prompt.name}'?",
            "Confirm Delete", wx.YES_NO | wx.ICON_QUESTION
        ) == wx.YES:
            if self.prompts_manager.remove_extra_prompt(prompt.id):
                if prompt.id in self.selected_extras:
                    del self.selected_extras[prompt.id]
                self._refresh_prompts()
            else:
                wx.MessageBox("Failed to delete extra prompt", "Error", wx.OK | wx.ICON_ERROR)
    
    def on_send_to_chat(self, event):
        """Send the built prompt to a new chat."""
        built_prompt = self.built_prompt_text.GetValue().strip()
        if not built_prompt:
            wx.MessageBox("Please build a prompt first", "No Prompt", wx.OK | wx.ICON_WARNING)
            return
        
        # Get the chat tab and start a new chat with this prompt
        chat_tab = self.main_window.tab_manager.get_tab_by_name('chat')
        if chat_tab:
            logger.info(f"Found chat tab: {chat_tab}")
            
            # Switch to chat tab
            tab_switched = False
            for i in range(self.main_window.notebook.GetPageCount()):
                page = self.main_window.notebook.GetPage(i)
                if page == chat_tab:
                    logger.info(f"Switching to chat tab at index {i}")
                    self.main_window.notebook.SetSelection(i)
                    tab_switched = True
                    break
            
            if not tab_switched:
                logger.error("Failed to find chat tab in notebook pages")
            
            # Start new chat and set the prompt
            chat_tab.start_new_chat()
            chat_tab.set_input_text(built_prompt)
            logger.info("Input text set in chat tab")
        else:
            wx.MessageBox("Chat tab not available", "Error", wx.OK | wx.ICON_ERROR)
    
    def on_send_to_batch(self, event):
        """Send the built prompt to the batch tab."""
        built_prompt = self.built_prompt_text.GetValue().strip()
        if not built_prompt:
            wx.MessageBox("Please build a prompt first", "No Prompt", wx.OK | wx.ICON_WARNING)
            return
        
        # Get the batch tab and set the prompt
        batch_tab = self.main_window.tab_manager.get_tab_by_name('batch')
        if batch_tab:
            logger.info(f"Found batch tab: {batch_tab}")
            
            # Switch to batch tab
            tab_switched = False
            for i in range(self.main_window.notebook.GetPageCount()):
                page = self.main_window.notebook.GetPage(i)
                if page == batch_tab:
                    logger.info(f"Switching to batch tab at index {i}")
                    self.main_window.notebook.SetSelection(i)
                    tab_switched = True
                    break
            
            if not tab_switched:
                logger.error("Failed to find batch tab in notebook pages")
            
            # Set the prompt in batch tab
            if hasattr(batch_tab, 'set_prompt_text'):
                batch_tab.set_prompt_text(built_prompt)
                logger.info("Prompt text set in batch tab")
            else:
                wx.MessageBox("Batch tab does not support prompt setting", "Error", wx.OK | wx.ICON_ERROR)
        else:
            wx.MessageBox("Batch tab not available", "Error", wx.OK | wx.ICON_ERROR)
    
    def on_copy_prompt(self, event):
        """Copy the built prompt to clipboard."""
        built_prompt = self.built_prompt_text.GetValue().strip()
        if not built_prompt:
            wx.MessageBox("Please build a prompt first", "No Prompt", wx.OK | wx.ICON_WARNING)
            return
        
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(built_prompt))
            wx.TheClipboard.Close()
            wx.MessageBox("Prompt copied to clipboard", "Success", wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox("Failed to access clipboard", "Error", wx.OK | wx.ICON_ERROR)
    
    def on_sync_defaults(self, event):
        """Sync prompts from the default llm_prompts.json file."""
        # Show progress dialog
        progress_dlg = wx.ProgressDialog(
            "Syncing Prompts",
            "Checking for new prompts in defaults...",
            maximum=100,
            parent=self,
            style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE
        )
        
        try:
            progress_dlg.Update(50, "Syncing from defaults...")
            
            # Perform sync
            added_counts = self.prompts_manager.sync_from_defaults()
            
            progress_dlg.Update(100, "Refreshing prompts...")
            
            # Refresh the UI
            self._refresh_prompts()
            
            # Show results
            total_added = added_counts['base'] + added_counts['extra']
            if total_added > 0:
                message = f"Successfully synced {total_added} new prompts:\n"
                message += f"• {added_counts['base']} base prompts\n"
                message += f"• {added_counts['extra']} extra prompts"
                wx.MessageBox(message, "Sync Complete", wx.OK | wx.ICON_INFORMATION)
            else:
                wx.MessageBox("No new prompts found in defaults.", "Sync Complete", wx.OK | wx.ICON_INFORMATION)
                
        except Exception as e:
            logger.error(f"Failed to sync prompts: {e}")
            wx.MessageBox(f"Failed to sync prompts: {e}", "Sync Error", wx.OK | wx.ICON_ERROR)
        finally:
            progress_dlg.Destroy()
    
    def refresh(self):
        """Refresh the prompts tab."""
        self.prompts_manager.load_config()
        self._refresh_prompts()
    
    def cleanup(self):
        """Clean up the prompts tab."""
        # Save any pending changes
        pass
