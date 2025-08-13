"""
Document Import Dialog for LlamaLot embeddings management.

Provides interface for importing documents from various sources (TXT, PDF, URL).
"""

import wx
import logging
import os
import threading
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import PyPDF2
import io
import uuid
from datetime import datetime

from llamalot.backend import Document
from llamalot.utils.logging_config import get_logger

logger = get_logger(__name__)


class DocumentImportDialog(wx.Dialog):
    """
    Dialog for importing documents from various sources.
    
    Supports:
    - Text files (.txt, .md)
    - PDF files (.pdf)
    - Web URLs
    - Batch processing
    """
    
    def __init__(self, parent):
        """
        Initialize the document import dialog.
        
        Args:
            parent: Parent window
        """
        super().__init__(
            parent,
            title="Import Documents",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        
        self.imported_documents: List[Document] = []
        self.import_thread = None
        
        self._create_widgets()
        self._create_layout()
        self._bind_events()
        
        logger.info("Document import dialog initialized")
    
    def _create_widgets(self):
        """Create all UI widgets."""
        
        # === Import Source Section ===
        source_box = wx.StaticBox(self, label="Import Source")
        self.source_sizer = wx.StaticBoxSizer(source_box, wx.VERTICAL)
        
        # Source type selection
        self.source_type = wx.RadioBox(
            self,
            label="Source Type",
            choices=["Text Files", "PDF Files", "Web URLs"],
            style=wx.RA_SPECIFY_ROWS
        )
        
        # === File Selection ===
        file_box = wx.StaticBox(self, label="File Selection")
        self.file_sizer = wx.StaticBoxSizer(file_box, wx.VERTICAL)
        
        # File list
        self.file_list = wx.ListCtrl(self, style=wx.LC_REPORT)
        self.file_list.AppendColumn("Source", width=300)
        self.file_list.AppendColumn("Type", width=80)
        self.file_list.AppendColumn("Status", width=100)
        
        # File management buttons
        file_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_add_files = wx.Button(self, label="Add Files")
        self.btn_add_url = wx.Button(self, label="Add URL")
        self.btn_remove_selected = wx.Button(self, label="Remove Selected")
        self.btn_clear_all = wx.Button(self, label="Clear All")
        
        file_btn_sizer.Add(self.btn_add_files, 0, wx.RIGHT, 5)
        file_btn_sizer.Add(self.btn_add_url, 0, wx.RIGHT, 5)
        file_btn_sizer.Add(self.btn_remove_selected, 0, wx.RIGHT, 5)
        file_btn_sizer.Add(self.btn_clear_all, 0)
        
        # === Import Options ===
        options_box = wx.StaticBox(self, label="Import Options")
        self.options_sizer = wx.StaticBoxSizer(options_box, wx.VERTICAL)
        
        # Document ID prefix
        id_sizer = wx.BoxSizer(wx.HORIZONTAL)
        id_sizer.Add(wx.StaticText(self, label="Document ID Prefix:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.id_prefix = wx.TextCtrl(self, value="imported")
        id_sizer.Add(self.id_prefix, 1)
        
        # Metadata options
        self.add_filename_metadata = wx.CheckBox(self, label="Add filename as metadata")
        self.add_source_metadata = wx.CheckBox(self, label="Add source path/URL as metadata")
        self.add_import_date = wx.CheckBox(self, label="Add import date as metadata")
        
        # Set defaults
        self.add_filename_metadata.SetValue(True)
        self.add_source_metadata.SetValue(True)
        self.add_import_date.SetValue(True)
        
        # Content processing options
        self.split_large_content = wx.CheckBox(self, label="Split large content into chunks")
        self.chunk_size_label = wx.StaticText(self, label="Chunk size (characters):")
        self.chunk_size = wx.SpinCtrl(self, min=100, max=10000, initial=2000)
        
        # Progress section
        progress_box = wx.StaticBox(self, label="Import Progress")
        self.progress_sizer = wx.StaticBoxSizer(progress_box, wx.VERTICAL)
        
        self.progress_gauge = wx.Gauge(self, range=100)
        self.progress_text = wx.StaticText(self, label="Ready to import...")
        
        # === Dialog Buttons ===
        self.btn_import = wx.Button(self, label="Start Import")
        self.btn_cancel = wx.Button(self, wx.ID_CANCEL, "Cancel")
        self.btn_close = wx.Button(self, wx.ID_OK, "Close")
        
        # Initially disable close button
        self.btn_close.Enable(False)
    
    def _create_layout(self):
        """Create the layout for all widgets."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Source selection
        self.source_sizer.Add(self.source_type, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.source_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # File selection
        self.file_sizer.Add(self.file_list, 1, wx.EXPAND | wx.ALL, 5)
        self.file_sizer.Add(file_btn_sizer, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.file_sizer, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        
        # Import options
        self.options_sizer.Add(id_sizer, 0, wx.EXPAND | wx.ALL, 5)
        self.options_sizer.Add(self.add_filename_metadata, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
        self.options_sizer.Add(self.add_source_metadata, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
        self.options_sizer.Add(self.add_import_date, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
        
        # Chunking options
        chunk_sizer = wx.BoxSizer(wx.HORIZONTAL)
        chunk_sizer.Add(self.split_large_content, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        chunk_sizer.Add(self.chunk_size_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        chunk_sizer.Add(self.chunk_size, 0)
        self.options_sizer.Add(chunk_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        main_sizer.Add(self.options_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        
        # Progress
        self.progress_sizer.Add(self.progress_gauge, 0, wx.EXPAND | wx.ALL, 5)
        self.progress_sizer.Add(self.progress_text, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        main_sizer.Add(self.progress_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        
        # Dialog buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.Add(self.btn_import, 0, wx.RIGHT, 5)
        btn_sizer.AddStretchSpacer()
        btn_sizer.Add(self.btn_cancel, 0, wx.RIGHT, 5)
        btn_sizer.Add(self.btn_close, 0)
        
        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        self.SetSizer(main_sizer)
        self.SetSize((600, 700))
    
    def _bind_events(self):
        """Bind all event handlers."""
        
        # Source type changes
        self.Bind(wx.EVT_RADIOBOX, self._on_source_type_changed, self.source_type)
        
        # File management
        self.Bind(wx.EVT_BUTTON, self._on_add_files, self.btn_add_files)
        self.Bind(wx.EVT_BUTTON, self._on_add_url, self.btn_add_url)
        self.Bind(wx.EVT_BUTTON, self._on_remove_selected, self.btn_remove_selected)
        self.Bind(wx.EVT_BUTTON, self._on_clear_all, self.btn_clear_all)
        
        # Import control
        self.Bind(wx.EVT_BUTTON, self._on_start_import, self.btn_import)
        
        # List selection
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self._on_file_selected, self.file_list)
        
        # Chunking option
        self.Bind(wx.EVT_CHECKBOX, self._on_chunking_changed, self.split_large_content)
        
        # Update chunking controls initially
        self._on_chunking_changed(None)
    
    def _update_file_buttons(self):
        """Update file management button states."""
        has_items = self.file_list.GetItemCount() > 0
        has_selection = self.file_list.GetFirstSelected() != -1
        
        self.btn_remove_selected.Enable(has_selection)
        self.btn_clear_all.Enable(has_items)
        self.btn_import.Enable(has_items)
    
    # === Event Handlers ===
    
    def _on_source_type_changed(self, event):
        """Handle source type selection change."""
        source_type = self.source_type.GetSelection()
        
        # Update button labels based on source type
        if source_type == 0:  # Text Files
            self.btn_add_files.SetLabel("Add Text Files")
        elif source_type == 1:  # PDF Files
            self.btn_add_files.SetLabel("Add PDF Files")
        else:  # Web URLs
            self.btn_add_files.SetLabel("Add Files")
    
    def _on_add_files(self, event):
        """Handle file selection."""
        source_type = self.source_type.GetSelection()
        
        if source_type == 0:  # Text Files
            wildcard = "Text files (*.txt;*.md)|*.txt;*.md|All files (*.*)|*.*"
        elif source_type == 1:  # PDF Files
            wildcard = "PDF files (*.pdf)|*.pdf|All files (*.*)|*.*"
        else:  # Any files
            wildcard = "All files (*.*)|*.*"
        
        with wx.FileDialog(
            self,
            message="Select files to import",
            wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_MULTIPLE | wx.FD_FILE_MUST_EXIST
        ) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                paths = dialog.GetPaths()
                for path in paths:
                    self._add_file_to_list(path)
                
                self._update_file_buttons()
    
    def _on_add_url(self, event):
        """Handle URL addition."""
        with wx.TextEntryDialog(
            self,
            "Enter URL to import:",
            "Add URL",
            ""
        ) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                url = dialog.GetValue().strip()
                if url:
                    # Basic URL validation
                    parsed = urlparse(url)
                    if parsed.scheme and parsed.netloc:
                        self._add_url_to_list(url)
                        self._update_file_buttons()
                    else:
                        wx.MessageBox(
                            "Please enter a valid URL (including http:// or https://)",
                            "Invalid URL",
                            wx.OK | wx.ICON_ERROR
                        )
    
    def _on_remove_selected(self, event):
        """Remove selected items from the list."""
        selection = self.file_list.GetFirstSelected()
        while selection != -1:
            self.file_list.DeleteItem(selection)
            selection = self.file_list.GetFirstSelected()
        
        self._update_file_buttons()
    
    def _on_clear_all(self, event):
        """Clear all items from the list."""
        self.file_list.DeleteAllItems()
        self._update_file_buttons()
    
    def _on_file_selected(self, event):
        """Handle file list selection."""
        self._update_file_buttons()
    
    def _on_chunking_changed(self, event):
        """Handle chunking option change."""
        enabled = self.split_large_content.GetValue()
        self.chunk_size_label.Enable(enabled)
        self.chunk_size.Enable(enabled)
    
    def _on_start_import(self, event):
        """Start the import process."""
        if self.import_thread and self.import_thread.is_alive():
            return
        
        # Disable controls during import
        self.btn_import.Enable(False)
        self.btn_add_files.Enable(False)
        self.btn_add_url.Enable(False)
        self.btn_remove_selected.Enable(False)
        self.btn_clear_all.Enable(False)
        
        # Start import thread
        self.import_thread = threading.Thread(target=self._import_worker)
        self.import_thread.daemon = True
        self.import_thread.start()
    
    def _add_file_to_list(self, file_path: str):
        """Add a file to the import list."""
        filename = os.path.basename(file_path)
        file_ext = os.path.splitext(filename)[1].lower()
        
        # Determine file type
        if file_ext in ['.txt', '.md']:
            file_type = "Text"
        elif file_ext == '.pdf':
            file_type = "PDF"
        else:
            file_type = "Unknown"
        
        # Add to list
        index = self.file_list.GetItemCount()
        self.file_list.InsertItem(index, file_path)
        self.file_list.SetItem(index, 1, file_type)
        self.file_list.SetItem(index, 2, "Pending")
        
        logger.info(f"Added file to import list: {file_path}")
    
    def _add_url_to_list(self, url: str):
        """Add a URL to the import list."""
        index = self.file_list.GetItemCount()
        self.file_list.InsertItem(index, url)
        self.file_list.SetItem(index, 1, "URL")
        self.file_list.SetItem(index, 2, "Pending")
        
        logger.info(f"Added URL to import list: {url}")
    
    def _import_worker(self):
        """Worker thread for importing documents."""
        try:
            total_items = self.file_list.GetItemCount()
            
            if total_items == 0:
                wx.CallAfter(self._update_progress, "No items to import", 100)
                return
            
            self.imported_documents.clear()
            
            for i in range(total_items):
                # Update progress
                progress = int((i / total_items) * 100)
                source = self.file_list.GetItemText(i, 0)
                source_type = self.file_list.GetItemText(i, 1)
                
                wx.CallAfter(self._update_progress, f"Processing: {os.path.basename(source)}", progress)
                wx.CallAfter(self._update_item_status, i, "Processing")
                
                try:
                    # Import based on type
                    if source_type == "URL":
                        documents = self._import_url(source)
                    elif source_type == "PDF":
                        documents = self._import_pdf(source)
                    else:  # Text
                        documents = self._import_text_file(source)
                    
                    self.imported_documents.extend(documents)
                    wx.CallAfter(self._update_item_status, i, f"Success ({len(documents)} docs)")
                    
                except Exception as e:
                    logger.error(f"Error importing {source}: {e}")
                    wx.CallAfter(self._update_item_status, i, f"Error: {str(e)[:30]}")
            
            # Final progress update
            wx.CallAfter(self._update_progress, f"Import complete: {len(self.imported_documents)} documents", 100)
            wx.CallAfter(self._import_completed)
            
        except Exception as e:
            logger.error(f"Import worker error: {e}")
            wx.CallAfter(self._update_progress, f"Import failed: {e}", 100)
            wx.CallAfter(self._import_completed)
    
    def _import_text_file(self, file_path: str) -> List[Document]:
        """Import a text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return self._create_documents_from_content(
                content=content,
                source=file_path,
                source_type="file",
                filename=os.path.basename(file_path)
            )
            
        except UnicodeDecodeError:
            # Try with latin-1 encoding as fallback
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            
            return self._create_documents_from_content(
                content=content,
                source=file_path,
                source_type="file",
                filename=os.path.basename(file_path)
            )
    
    def _import_pdf(self, file_path: str) -> List[Document]:
        """Import a PDF file."""
        content_parts = []
        
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        content_parts.append(f"[Page {page_num + 1}]\n{page_text}")
                except Exception as e:
                    logger.warning(f"Error extracting page {page_num + 1} from {file_path}: {e}")
        
        content = "\n\n".join(content_parts)
        
        return self._create_documents_from_content(
            content=content,
            source=file_path,
            source_type="pdf",
            filename=os.path.basename(file_path)
        )
    
    def _import_url(self, url: str) -> List[Document]:
        """Import content from a URL."""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            content = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in content.splitlines())
            content = '\n'.join(line for line in lines if line)
            
            return self._create_documents_from_content(
                content=content,
                source=url,
                source_type="url",
                filename=urlparse(url).netloc
            )
            
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch URL: {e}")
    
    def _create_documents_from_content(
        self,
        content: str,
        source: str,
        source_type: str,
        filename: str
    ) -> List[Document]:
        """Create documents from content, optionally splitting into chunks."""
        
        if not content.strip():
            return []
        
        documents = []
        prefix = self.id_prefix.GetValue().strip()
        
        # Common metadata
        base_metadata = {}
        
        if self.add_filename_metadata.GetValue():
            base_metadata['filename'] = filename
        
        if self.add_source_metadata.GetValue():
            base_metadata['source'] = source
            base_metadata['source_type'] = source_type
        
        if self.add_import_date.GetValue():
            base_metadata['import_date'] = datetime.now().isoformat()
        
        # Check if we should split content
        if self.split_large_content.GetValue() and len(content) > self.chunk_size.GetValue():
            chunk_size = self.chunk_size.GetValue()
            chunks = self._split_content(content, chunk_size)
            
            for i, chunk in enumerate(chunks):
                doc_id = f"{prefix}_{uuid.uuid4().hex[:8]}_part{i+1}"
                
                metadata = base_metadata.copy()
                metadata['chunk_index'] = i + 1
                metadata['total_chunks'] = len(chunks)
                
                documents.append(Document(
                    id=doc_id,
                    content=chunk,
                    metadata=metadata
                ))
        else:
            # Single document
            doc_id = f"{prefix}_{uuid.uuid4().hex[:8]}"
            
            documents.append(Document(
                id=doc_id,
                content=content,
                metadata=base_metadata
            ))
        
        return documents
    
    def _split_content(self, content: str, chunk_size: int) -> List[str]:
        """Split content into chunks, trying to break at sentence boundaries."""
        chunks = []
        current_chunk = ""
        
        # Split by sentences first
        sentences = content.replace('. ', '.\n').split('\n')
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # If adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                chunks.append(current_chunk)
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
        
        # Add remaining content
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _update_progress(self, message: str, progress: int):
        """Update progress display (thread-safe)."""
        self.progress_text.SetLabel(message)
        self.progress_gauge.SetValue(progress)
    
    def _update_item_status(self, index: int, status: str):
        """Update item status in the list (thread-safe)."""
        self.file_list.SetItem(index, 2, status)
    
    def _import_completed(self):
        """Handle import completion (thread-safe)."""
        # Re-enable controls
        self.btn_add_files.Enable(True)
        self.btn_add_url.Enable(True)
        self._update_file_buttons()
        
        # Enable close button
        self.btn_close.Enable(True)
        
        logger.info(f"Import completed: {len(self.imported_documents)} documents imported")
    
    def get_imported_documents(self) -> List[Document]:
        """
        Get the list of imported documents.
        
        Returns:
            List of imported Document objects
        """
        return self.imported_documents.copy()
