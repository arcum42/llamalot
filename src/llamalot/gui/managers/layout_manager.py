"""
Layout manager for LlamaLot application.

Handles window layout creation and management including
the main splitter window and tab notebook.
"""

import wx
from typing import Optional, Dict, Any

from llamalot.utils.logging_config import get_logger

logger = get_logger(__name__)


class LayoutManager:
    """Manages the main window layout and components."""
    
    def __init__(self, parent_window: wx.Frame):
        """Initialize the layout manager."""
        self.parent = parent_window
        self.main_panel: Optional[wx.Panel] = None
        self.splitter: Optional[wx.SplitterWindow] = None
        self.notebook: Optional[wx.Notebook] = None
        self.status_bar: Optional[wx.StatusBar] = None
        
        # Layout components
        self.sizers = {}
        self.panels = {}
    
    def create_main_layout(self) -> wx.Panel:
        """Create and return the main window layout."""
        if self.main_panel:
            return self.main_panel
            
        # Create main panel
        self.main_panel = wx.Panel(self.parent)
        
        # Create main sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizers['main'] = main_sizer
        
        # Create toolbar if needed
        # toolbar = self._create_toolbar()
        # if toolbar:
        #     main_sizer.Add(toolbar, 0, wx.EXPAND)
        
        # Create splitter window
        self.splitter = wx.SplitterWindow(
            self.main_panel,
            style=wx.SP_3D | wx.SP_LIVE_UPDATE
        )
        self.splitter.SetMinimumPaneSize(200)
        
        # Create notebook for tabs
        self.notebook = wx.Notebook(self.splitter)
        
        # Add notebook to splitter for now (can add sidebar later)
        self.splitter.Initialize(self.notebook)
        
        # Add splitter to main sizer
        main_sizer.Add(self.splitter, 1, wx.EXPAND | wx.ALL, 5)
        
        # Create status bar
        self._create_status_bar()
        
        # Set sizer
        self.main_panel.SetSizer(main_sizer)
        
        logger.info("Main layout created")
        return self.main_panel
    
    def _create_status_bar(self) -> None:
        """Create the status bar."""
        self.status_bar = self.parent.CreateStatusBar(3)
        self.status_bar.SetStatusWidths([-2, -1, -1])
        self.status_bar.SetStatusText("Ready", 0)
        self.status_bar.SetStatusText("", 1)
        self.status_bar.SetStatusText("", 2)
    
    def add_tab(self, panel: wx.Panel, title: str, select: bool = False) -> int:
        """Add a tab to the notebook."""
        if not self.notebook:
            logger.error("Notebook not initialized")
            return -1
            
        page_index = self.notebook.GetPageCount()
        self.notebook.AddPage(panel, title, select)
        
        logger.info(f"Added tab '{title}' at index {page_index}")
        return page_index
    
    def remove_tab(self, index: int) -> bool:
        """Remove a tab from the notebook."""
        if not self.notebook or index < 0 or index >= self.notebook.GetPageCount():
            return False
            
        title = self.notebook.GetPageText(index)
        self.notebook.DeletePage(index)
        
        logger.info(f"Removed tab '{title}' at index {index}")
        return True
    
    def select_tab(self, index: int) -> bool:
        """Select a tab by index."""
        if not self.notebook or index < 0 or index >= self.notebook.GetPageCount():
            return False
            
        self.notebook.SetSelection(index)
        return True
    
    def select_tab_by_title(self, title: str) -> bool:
        """Select a tab by title."""
        if not self.notebook:
            return False
            
        for i in range(self.notebook.GetPageCount()):
            if self.notebook.GetPageText(i) == title:
                self.notebook.SetSelection(i)
                return True
        return False
    
    def get_current_tab_index(self) -> int:
        """Get the index of the currently selected tab."""
        if not self.notebook:
            return -1
        return self.notebook.GetSelection()
    
    def get_current_tab_title(self) -> str:
        """Get the title of the currently selected tab."""
        if not self.notebook:
            return ""
        index = self.notebook.GetSelection()
        if index >= 0:
            return self.notebook.GetPageText(index)
        return ""
    
    def get_tab_count(self) -> int:
        """Get the number of tabs."""
        if not self.notebook:
            return 0
        return self.notebook.GetPageCount()
    
    def update_status_bar(self, message: str, field: int = 0) -> None:
        """Update the status bar message."""
        if self.status_bar and 0 <= field < self.status_bar.GetFieldsCount():
            self.status_bar.SetStatusText(message, field)
    
    def set_status_fields(self, messages: list) -> None:
        """Set multiple status bar fields at once."""
        if not self.status_bar:
            return
            
        for i, message in enumerate(messages):
            if i < self.status_bar.GetFieldsCount():
                self.status_bar.SetStatusText(message, i)
    
    def create_sidebar(self, width: int = 250) -> Optional[wx.Panel]:
        """Create a sidebar panel (not implemented yet)."""
        # This would split the splitter to have a sidebar
        # For now, return None as we're using single-pane layout
        return None
    
    def toggle_sidebar(self) -> None:
        """Toggle sidebar visibility (not implemented yet)."""
        # This would show/hide the sidebar panel
        pass
    
    def get_splitter_position(self) -> int:
        """Get the current splitter position."""
        if self.splitter and self.splitter.IsSplit():
            return self.splitter.GetSashPosition()
        return 0
    
    def set_splitter_position(self, position: int) -> None:
        """Set the splitter position."""
        if self.splitter and self.splitter.IsSplit():
            self.splitter.SetSashPosition(position)
    
    def save_layout_state(self) -> Dict[str, Any]:
        """Save the current layout state."""
        state = {
            'splitter_position': self.get_splitter_position(),
            'current_tab': self.get_current_tab_index(),
            'tab_count': self.get_tab_count()
        }
        return state
    
    def restore_layout_state(self, state: Dict[str, Any]) -> None:
        """Restore the layout state."""
        if 'splitter_position' in state and state['splitter_position'] > 0:
            self.set_splitter_position(state['splitter_position'])
            
        if 'current_tab' in state and state['current_tab'] >= 0:
            self.select_tab(state['current_tab'])
