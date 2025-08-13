"""
Menu manager for LlamaLot application.

Handles creation and management of the application menu bar
and associated event handlers.
"""

import wx
from typing import Optional, Callable

from llamalot.utils.logging_config import get_logger

logger = get_logger(__name__)


class MenuManager:
    """Manages the application menu bar and events."""
    
    def __init__(self, parent_window: wx.Frame):
        """Initialize the menu manager."""
        self.parent = parent_window
        self.menu_bar: Optional[wx.MenuBar] = None
        
        # Menu event callbacks
        self.callbacks = {}
    
    def create_menu_bar(self) -> wx.MenuBar:
        """Create and return the application menu bar."""
        if self.menu_bar:
            return self.menu_bar
            
        self.menu_bar = wx.MenuBar()
        
        # Create menus
        self._create_file_menu()
        self._create_edit_menu()
        self._create_view_menu()
        self._create_help_menu()
        
        return self.menu_bar
    
    def _create_file_menu(self) -> None:
        """Create the File menu."""
        file_menu = wx.Menu()
        
        # New Chat
        file_menu.Append(wx.ID_ANY, "New Chat\tCtrl+N", "Start a new chat conversation")
        
        file_menu.AppendSeparator()
        
        # Model Management
        file_menu.Append(wx.ID_ANY, "Pull Model...", "Download a new model")
        file_menu.Append(wx.ID_ANY, "Create Model...\tCtrl+Shift+N", "Create a custom model")
        file_menu.Append(wx.ID_ANY, "Delete Model...", "Delete selected model")
        file_menu.Append(wx.ID_ANY, "Stop Model...", "Stop/unload selected model from memory")
        
        file_menu.AppendSeparator()
        
        # Export
        file_menu.Append(wx.ID_ANY, "Export Chat...\tCtrl+E", "Export current chat")
        
        file_menu.AppendSeparator()
        
        # Exit
        file_menu.Append(wx.ID_EXIT, "Exit\tCtrl+Q", "Exit the application")
        
        self.menu_bar.Append(file_menu, "File")
    
    def _create_edit_menu(self) -> None:
        """Create the Edit menu."""
        edit_menu = wx.Menu()
        
        # Add Undo/Redo but disable them since they don't work reliably
        undo_item = edit_menu.Append(wx.ID_UNDO, "Undo\tCtrl+Z", "Undo last action")
        redo_item = edit_menu.Append(wx.ID_REDO, "Redo\tCtrl+Y", "Redo last action")
        undo_item.Enable(False)
        redo_item.Enable(False)
        edit_menu.AppendSeparator()
        
        edit_menu.Append(wx.ID_CUT, "Cut\tCtrl+X", "Cut selected text")
        edit_menu.Append(wx.ID_COPY, "Copy\tCtrl+C", "Copy selected text")
        edit_menu.Append(wx.ID_PASTE, "Paste\tCtrl+V", "Paste text from clipboard")
        
        edit_menu.AppendSeparator()
        
        # Settings
        edit_menu.Append(wx.ID_PREFERENCES, "Settings...\tCtrl+,", "Open application settings")
        
        self.menu_bar.Append(edit_menu, "Edit")
    
    def _create_view_menu(self) -> None:
        """Create the View menu."""
        view_menu = wx.Menu()
        
        # Tab switching in the same order as tabs are created
        view_menu.Append(wx.ID_ANY, "Models Tab\tCtrl+1", "Switch to Models tab")
        view_menu.Append(wx.ID_ANY, "Chat Tab\tCtrl+2", "Switch to Chat tab")
        view_menu.Append(wx.ID_ANY, "Batch Tab\tCtrl+3", "Switch to Batch tab")
        view_menu.Append(wx.ID_ANY, "Embeddings Tab\tCtrl+4", "Switch to Embeddings tab")
        view_menu.Append(wx.ID_ANY, "History Tab\tCtrl+5", "Switch to History tab")
        
        view_menu.AppendSeparator()
        
        view_menu.Append(wx.ID_ANY, "Refresh All\tF5", "Refresh all data")
        view_menu.Append(wx.ID_ANY, "Toggle Fullscreen\tF11", "Toggle fullscreen mode")
        
        self.menu_bar.Append(view_menu, "View")
    
    def _create_help_menu(self) -> None:
        """Create the Help menu."""
        help_menu = wx.Menu()
        
        help_menu.Append(wx.ID_ANY, "User Guide", "Open user guide")
        help_menu.Append(wx.ID_ANY, "Keyboard Shortcuts", "View keyboard shortcuts")
        help_menu.AppendSeparator()
        
        help_menu.Append(wx.ID_ANY, "Report Issue", "Report a bug or issue")
        help_menu.Append(wx.ID_ANY, "Feature Request", "Request a new feature")
        help_menu.AppendSeparator()
        
        help_menu.Append(wx.ID_ABOUT, "About LlamaLot", "About this application")
        
        self.menu_bar.Append(help_menu, "Help")
    
    def bind_menu_events(self, event_handlers: dict) -> None:
        """Bind menu events to their handlers."""
        self.callbacks.update(event_handlers)
        
        # Find and bind menu items
        for menu_pos in range(self.menu_bar.GetMenuCount()):
            menu = self.menu_bar.GetMenu(menu_pos)
            self._bind_menu_items(menu)
    
    def _bind_menu_items(self, menu: wx.Menu) -> None:
        """Recursively bind menu items to their handlers."""
        for item in menu.GetMenuItems():
            if item.IsSubMenu():
                self._bind_menu_items(item.GetSubMenu())
            elif item.GetId() != wx.ID_SEPARATOR:
                item_id = item.GetId()
                label = item.GetItemLabel().replace("&", "").split("\t")[0]
                
                # Look for handler by ID or label
                handler = self.callbacks.get(item_id) or self.callbacks.get(label)
                if handler:
                    self.parent.Bind(wx.EVT_MENU, handler, id=item_id)
                    logger.debug(f"Bound menu item '{label}' to handler")
    
    def get_menu_item_by_label(self, label: str) -> Optional[wx.MenuItem]:
        """Find a menu item by its label."""
        if not self.menu_bar:
            return None
            
        for menu_pos in range(self.menu_bar.GetMenuCount()):
            menu = self.menu_bar.GetMenu(menu_pos)
            item = self._find_menu_item_by_label(menu, label)
            if item:
                return item
        return None
    
    def _find_menu_item_by_label(self, menu: wx.Menu, label: str) -> Optional[wx.MenuItem]:
        """Recursively find a menu item by label."""
        for item in menu.GetMenuItems():
            if item.IsSubMenu():
                found = self._find_menu_item_by_label(item.GetSubMenu(), label)
                if found:
                    return found
            elif item.GetItemLabel().replace("&", "").split("\t")[0] == label:
                return item
        return None
    
    def enable_menu_item(self, label: str, enabled: bool = True) -> None:
        """Enable or disable a menu item by label."""
        item = self.get_menu_item_by_label(label)
        if item:
            item.Enable(enabled)
    
    def check_menu_item(self, label: str, checked: bool = True) -> None:
        """Check or uncheck a menu item by label."""
        item = self.get_menu_item_by_label(label)
        if item and item.IsCheckable():
            item.Check(checked)
