"""
Tab components for LlamaLot GUI.

This package contains individual tab implementations that were extracted
from the main window for better code organization and maintainability.
"""

from .history_tab import HistoryTab
from .embeddings_tab import EmbeddingsTab
from .batch_tab import BatchTab

__all__ = ['HistoryTab', 'EmbeddingsTab', 'BatchTab']
