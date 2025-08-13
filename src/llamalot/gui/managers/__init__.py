"""
Manager package for LlamaLot GUI components.

Contains managers for backend, menu, layout, and tab handling.
"""

from .backend_manager import BackendManager
from .menu_manager import MenuManager
from .layout_manager import LayoutManager
from .tab_manager import TabManager

__all__ = ['BackendManager', 'MenuManager', 'LayoutManager', 'TabManager']
