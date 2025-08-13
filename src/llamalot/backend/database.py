"""
Database management for LlamaLot application.

Provides SQLite-based caching for model information, conversation history,
and application state with schema migrations and transaction management.
"""

import logging
import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Generator, Tuple

from llamalot.models import OllamaModel, ChatMessage, ChatConversation
from llamalot.utils.logging_config import get_logger

logger = get_logger(__name__)


class DatabaseError(Exception):
    """Base exception for database operations."""
    pass


class MigrationError(DatabaseError):
    """Exception raised during database migrations."""
    pass


class DatabaseManager:
    """
    Manages SQLite database for caching and persistence.
    
    Handles model information, conversation history, application state,
    and provides schema migrations and transaction management.
    """
    
    # Current database schema version
    SCHEMA_VERSION = 4  # Fixed foreign key reference in messages table
    
    def __init__(self, db_path: Path):
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self._lock = threading.RLock()
        self._connection_pool = {}  # Thread-local connections
        
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Database manager initialized: {self.db_path}")
        
        # Initialize database schema
        self._initialize_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        Get a thread-local database connection.
        
        Returns:
            SQLite connection for the current thread
        """
        thread_id = threading.get_ident()
        
        if thread_id not in self._connection_pool:
            conn = sqlite3.connect(
                str(self.db_path),
                timeout=30.0,
                isolation_level=None  # Autocommit mode
            )
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            
            self._connection_pool[thread_id] = conn
            logger.debug(f"Created new database connection for thread {thread_id}")
        
        return self._connection_pool[thread_id]
    
    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Context manager for database transactions.
        
        Yields:
            SQLite connection with transaction management
        """
        conn = self._get_connection()
        
        try:
            conn.execute("BEGIN")
            yield conn
            conn.execute("COMMIT")
            logger.debug("Transaction committed successfully")
        except Exception as e:
            conn.execute("ROLLBACK")
            logger.error(f"Transaction rolled back due to error: {e}")
            raise
    
    def _initialize_database(self) -> None:
        """Initialize database schema and perform migrations."""
        with self._lock:
            conn = self._get_connection()
            
            # Create metadata table if it doesn't exist
            conn.execute("""
                CREATE TABLE IF NOT EXISTS db_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Check current schema version
            current_version = self._get_schema_version()
            logger.info(f"Current database schema version: {current_version}")
            
            if current_version < self.SCHEMA_VERSION:
                logger.info(f"Migrating database from version {current_version} to {self.SCHEMA_VERSION}")
                self._migrate_database(current_version)
            elif current_version > self.SCHEMA_VERSION:
                raise MigrationError(
                    f"Database schema version {current_version} is newer than "
                    f"supported version {self.SCHEMA_VERSION}"
                )
            
            # Clean up any models with invalid names
            self.cleanup_invalid_models()
    def _get_schema_version(self) -> int:
        """Get the current schema version from the database."""
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT value FROM db_metadata WHERE key = 'schema_version'"
        )
        row = cursor.fetchone()
        return int(row['value']) if row else 0
    
    def _set_schema_version(self, version: int) -> None:
        """Set the schema version in the database."""
        conn = self._get_connection()
        conn.execute("""
            INSERT OR REPLACE INTO db_metadata (key, value, updated_at)
            VALUES ('schema_version', ?, CURRENT_TIMESTAMP)
        """, (str(version),))
    
    def _migrate_database(self, from_version: int) -> None:
        """
        Perform database migration from the given version.
        
        Args:
            from_version: Current schema version to migrate from
        """
        try:
            with self.transaction() as conn:
                if from_version == 0:
                    self._create_initial_schema(conn)
                
                # Migration from v1 to v2: Add capabilities column
                if from_version == 1:
                    self._migrate_v1_to_v2(conn)
                
                # Migration from v2 to v3: Remove foreign key constraint on model_name in conversations
                if from_version == 2:
                    self._migrate_v2_to_v3(conn)
                
                # Migration from v3 to v4: Fix foreign key reference in messages table
                if from_version == 3:
                    self._migrate_v3_to_v4(conn)
                
                self._set_schema_version(self.SCHEMA_VERSION)
                logger.info(f"Database migration completed successfully")
                
        except Exception as e:
            logger.error(f"Database migration failed: {e}")
            raise MigrationError(f"Failed to migrate database: {e}")
    
    def _migrate_v1_to_v2(self, conn: sqlite3.Connection) -> None:
        """Migrate database from version 1 to version 2."""
        logger.info("Migrating database from v1 to v2: Adding capabilities column")
        
        # Add capabilities column to models table
        conn.execute("ALTER TABLE models ADD COLUMN capabilities TEXT")
        
        logger.info("Successfully added capabilities column to models table")
    
    def _migrate_v2_to_v3(self, conn: sqlite3.Connection) -> None:
        """Migrate database from version 2 to version 3."""
        logger.info("Migrating database from v2 to v3: Removing foreign key constraint on conversations.model_name")
        
        # SQLite doesn't support dropping foreign key constraints directly
        # We need to recreate the conversations table without the foreign key constraint
        
        # Step 1: Rename the current table
        conn.execute("ALTER TABLE conversations RENAME TO conversations_old")
        
        # Step 2: Create new conversations table without foreign key constraint
        conn.execute("""
            CREATE TABLE conversations (
                conversation_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                model_name TEXT,
                system_prompt TEXT,
                total_tokens INTEGER DEFAULT 0,
                total_time REAL DEFAULT 0.0,
                message_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Step 3: Copy data from old table to new table
        conn.execute("""
            INSERT INTO conversations 
            SELECT * FROM conversations_old
        """)
        
        # Step 4: Drop the old table
        conn.execute("DROP TABLE conversations_old")
        
        # Step 5: Recreate indexes
        conn.execute("CREATE INDEX idx_conversations_updated ON conversations(updated_at)")
        
        logger.info("Successfully removed foreign key constraint from conversations table")
    
    def _migrate_v3_to_v4(self, conn: sqlite3.Connection) -> None:
        """Migrate database from version 3 to version 4."""
        logger.info("Migrating database from v3 to v4: Fixing foreign key reference in messages table")
        
        # The messages table still references 'conversations_old' instead of 'conversations'
        # We need to recreate the messages table with the correct foreign key reference
        
        # Step 1: Rename the current messages table
        conn.execute("ALTER TABLE messages RENAME TO messages_old")
        
        # Step 2: Create new messages table with correct foreign key reference
        conn.execute("""
            CREATE TABLE messages (
                message_id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                
                -- Metadata
                model_name TEXT,
                tokens_used INTEGER,
                generation_time REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Error information
                error TEXT,
                is_error BOOLEAN DEFAULT 0,
                
                -- Message order in conversation
                sequence_number INTEGER NOT NULL,
                
                FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id) ON DELETE CASCADE
            )
        """)
        
        # Step 3: Copy data from old table to new table
        conn.execute("""
            INSERT INTO messages 
            SELECT * FROM messages_old
        """)
        
        # Step 4: Drop the old table
        conn.execute("DROP TABLE messages_old")
        
        # Step 5: Recreate indexes
        conn.execute("CREATE INDEX idx_messages_conversation ON messages(conversation_id)")
        conn.execute("CREATE INDEX idx_messages_timestamp ON messages(timestamp)")
        conn.execute("CREATE INDEX idx_messages_sequence ON messages(conversation_id, sequence_number)")
        
        logger.info("Successfully fixed foreign key reference in messages table")
    
    def _create_initial_schema(self, conn: sqlite3.Connection) -> None:
        """Create the initial database schema."""
        logger.info("Creating initial database schema")
        
        # Models table
        conn.execute("""
            CREATE TABLE models (
                name TEXT PRIMARY KEY,
                size INTEGER,
                digest TEXT,
                modified_at TIMESTAMP,
                
                -- Model details
                format TEXT,
                family TEXT,
                families TEXT,  -- JSON array
                parameter_size TEXT,
                quantization_level TEXT,
                
                -- Model info (from show command)
                modelfile TEXT,
                parameters TEXT,
                template TEXT,
                system TEXT,
                
                -- Cached capabilities
                capabilities TEXT,  -- JSON array of capabilities
                
                -- Metadata
                is_cached BOOLEAN DEFAULT 1,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Conversations table
        conn.execute("""
            CREATE TABLE conversations (
                conversation_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                model_name TEXT,
                system_prompt TEXT,
                
                -- Statistics
                total_tokens INTEGER DEFAULT 0,
                total_time REAL DEFAULT 0.0,
                message_count INTEGER DEFAULT 0,
                
                -- Timestamps
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Messages table
        conn.execute("""
            CREATE TABLE messages (
                message_id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                
                -- Metadata
                model_name TEXT,
                tokens_used INTEGER,
                generation_time REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Error information
                error TEXT,
                is_error BOOLEAN DEFAULT 0,
                
                -- Message order in conversation
                sequence_number INTEGER NOT NULL,
                
                FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id) ON DELETE CASCADE
            )
        """)
        
        # Message attachments table (for images, files, etc.)
        conn.execute("""
            CREATE TABLE message_attachments (
                attachment_id TEXT PRIMARY KEY,
                message_id TEXT NOT NULL,
                attachment_type TEXT NOT NULL,  -- 'image', 'file', etc.
                
                -- Attachment data
                data TEXT,  -- Base64 encoded data or file path
                filename TEXT,
                mime_type TEXT,
                size INTEGER,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (message_id) REFERENCES messages(message_id) ON DELETE CASCADE
            )
        """)
        
        # Application state table
        conn.execute("""
            CREATE TABLE app_state (
                key TEXT PRIMARY KEY,
                value TEXT,
                value_type TEXT DEFAULT 'string',  -- 'string', 'json', 'int', 'float', 'bool'
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for better performance
        conn.execute("CREATE INDEX idx_models_family ON models(family)")
        conn.execute("CREATE INDEX idx_models_last_accessed ON models(last_accessed)")
        conn.execute("CREATE INDEX idx_conversations_model ON conversations(model_name)")
        conn.execute("CREATE INDEX idx_conversations_updated ON conversations(updated_at)")
        conn.execute("CREATE INDEX idx_messages_conversation ON messages(conversation_id)")
        conn.execute("CREATE INDEX idx_messages_timestamp ON messages(timestamp)")
        conn.execute("CREATE INDEX idx_messages_sequence ON messages(conversation_id, sequence_number)")
        conn.execute("CREATE INDEX idx_attachments_message ON message_attachments(message_id)")
        
        logger.info("Initial database schema created successfully")
    
    # Model management methods
    def save_model(self, model: OllamaModel) -> None:
        """
        Save or update a model in the database.
        
        Args:
            model: OllamaModel instance to save
        """
        with self.transaction() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO models (
                    name, size, digest, modified_at,
                    format, family, families, parameter_size, quantization_level,
                    modelfile, parameters, template, system, capabilities,
                    last_accessed, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                model.name,
                model.size,
                model.digest,
                model.modified_at.isoformat() if model.modified_at else None,
                model.details.format,
                model.details.family,
                json.dumps(model.details.families) if model.details.families else None,
                model.details.parameter_size,
                model.details.quantization_level,
                model.model_info.architecture if model.model_info else None,  # Use architecture as modelfile
                json.dumps(model.model_info.__dict__) if model.model_info else None,  # Store all info as JSON in parameters
                None,  # template - not available in ModelInfo
                None,  # system - not available in ModelInfo
                json.dumps(model.capabilities) if model.capabilities else None,  # Store capabilities as JSON
            ))
        
        logger.debug(f"Saved model to database: {model.name}")
    
    def _parse_families(self, families_data: Optional[str]) -> List[str]:
        """Parse families data from database, handling both old and new formats."""
        if not families_data:
            return []
        
        try:
            # Try JSON first (new format)
            return json.loads(families_data)
        except (json.JSONDecodeError, TypeError):
            try:
                # Try eval for old string format (less safe but backwards compatible)
                result = eval(families_data)
                return result if isinstance(result, list) else []
            except:
                # If all else fails, return empty list
                return []
    
    def _parse_capabilities(self, capabilities_data: Optional[str]) -> List[str]:
        """Parse capabilities data from database."""
        if not capabilities_data:
            return []
        
        try:
            return json.loads(capabilities_data)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def get_model(self, name: str) -> Optional[OllamaModel]:
        """
        Retrieve a model from the database.
        
        Args:
            name: Model name
            
        Returns:
            OllamaModel instance or None if not found
        """
        conn = self._get_connection()
        cursor = conn.execute("SELECT * FROM models WHERE name = ?", (name,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        # Update last accessed timestamp
        conn.execute(
            "UPDATE models SET last_accessed = CURRENT_TIMESTAMP WHERE name = ?",
            (name,)
        )
        
        # Convert row to OllamaModel
        model = self._row_to_model(row)
        logger.debug(f"Retrieved model from database: {name}")
        return model
    
    def list_models(self, family_filter: Optional[str] = None) -> List[OllamaModel]:
        """
        List all models in the database.
        
        Args:
            family_filter: Optional family filter
            
        Returns:
            List of OllamaModel instances
        """
        conn = self._get_connection()
        
        if family_filter:
            cursor = conn.execute(
                "SELECT * FROM models WHERE family = ? AND name != '' AND name IS NOT NULL ORDER BY name",
                (family_filter,)
            )
        else:
            cursor = conn.execute("SELECT * FROM models WHERE name != '' AND name IS NOT NULL ORDER BY name")
        
        models = [self._row_to_model(row) for row in cursor.fetchall()]
        logger.debug(f"Listed {len(models)} models from database")
        return models
    
    def cleanup_invalid_models(self) -> int:
        """
        Remove models with empty or null names from the database.
        
        Returns:
            Number of models removed
        """
        conn = self._get_connection()
        cursor = conn.execute("DELETE FROM models WHERE name = '' OR name IS NULL")
        removed_count = cursor.rowcount
        conn.commit()
        
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} models with invalid names")
        
        return removed_count
    
    def delete_model(self, name: str) -> bool:
        """
        Delete a model from the database.
        
        Args:
            name: Model name
            
        Returns:
            True if deleted, False if not found
        """
        with self.transaction() as conn:
            cursor = conn.execute("DELETE FROM models WHERE name = ?", (name,))
            deleted = cursor.rowcount > 0
        
        if deleted:
            logger.debug(f"Deleted model from database: {name}")
        
        return deleted
    
    def _row_to_model(self, row: sqlite3.Row) -> OllamaModel:
        """Convert database row to OllamaModel instance."""
        from llamalot.models.ollama_model import ModelDetails, ModelInfo
        
        # Parse datetime
        modified_at = datetime.now()  # Default to current time
        if row['modified_at']:
            try:
                modified_at = datetime.fromisoformat(row['modified_at'])
            except ValueError:
                pass  # Keep default
        
        # Create model details
        details = ModelDetails(
            format=row['format'] or "",
            family=row['family'] or "",
            families=self._parse_families(row['families']),
            parameter_size=row['parameter_size'],
            quantization_level=row['quantization_level']
        )
        
        # Create model info if available
        model_info = None
        if row['parameters']:  # We stored the JSON data in parameters column
            try:
                info_data = json.loads(row['parameters'])
                model_info = ModelInfo()
                # Set fields from the stored data
                for key, value in info_data.items():
                    if hasattr(model_info, key):
                        setattr(model_info, key, value)
            except (json.JSONDecodeError, TypeError):
                # If JSON parsing fails, create basic ModelInfo with architecture
                if row['modelfile']:  # architecture stored in modelfile column
                    model_info = ModelInfo(architecture=row['modelfile'])
        
        # Restore capabilities from cache
        capabilities = self._parse_capabilities(row['capabilities']) if row['capabilities'] else []
        
        model = OllamaModel(
            name=row['name'],
            size=row['size'],
            digest=row['digest'],
            modified_at=modified_at,
            details=details,
            model_info=model_info
        )
        
        # Set cached capabilities
        model.capabilities = capabilities
        
        return model
    
    # Conversation management methods
    def save_conversation(self, conversation: ChatConversation) -> None:
        """
        Save or update a conversation in the database.
        
        Args:
            conversation: ChatConversation instance to save
        """
        with self.transaction() as conn:
            # Save conversation metadata
            conn.execute("""
                INSERT OR REPLACE INTO conversations (
                    conversation_id, title, model_name, system_prompt,
                    total_tokens, total_time, message_count,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                conversation.conversation_id,
                conversation.title,
                conversation.model_name,
                conversation.system_prompt,
                conversation.total_tokens,
                conversation.total_time,
                len(conversation.messages),
                conversation.created_at.isoformat(),
                conversation.updated_at.isoformat(),
            ))
            
            # Delete existing messages for this conversation
            conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation.conversation_id,))
            
            # Save messages
            for i, message in enumerate(conversation.messages):
                self._save_message(conn, message, conversation.conversation_id, i)
        
        logger.debug(f"Saved conversation to database: {conversation.conversation_id}")
    
    def get_conversation(self, conversation_id: str) -> Optional[ChatConversation]:
        """
        Retrieve a conversation from the database.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            ChatConversation instance or None if not found
        """
        conn = self._get_connection()
        
        # Get conversation metadata
        cursor = conn.execute("SELECT * FROM conversations WHERE conversation_id = ?", (conversation_id,))
        conv_row = cursor.fetchone()
        
        if not conv_row:
            return None
        
        # Get messages
        cursor = conn.execute("""
            SELECT * FROM messages 
            WHERE conversation_id = ? 
            ORDER BY sequence_number
        """, (conversation_id,))
        
        messages = []
        for msg_row in cursor.fetchall():
            message = self._row_to_message(msg_row)
            messages.append(message)
        
        # Create conversation
        conversation = ChatConversation(
            conversation_id=conv_row['conversation_id'],
            title=conv_row['title'],
            model_name=conv_row['model_name'],
            system_prompt=conv_row['system_prompt'],
            total_tokens=conv_row['total_tokens'],
            total_time=conv_row['total_time'],
            created_at=datetime.fromisoformat(conv_row['created_at']),
            updated_at=datetime.fromisoformat(conv_row['updated_at'])
        )
        
        conversation.messages = messages
        
        logger.debug(f"Retrieved conversation from database: {conversation_id}")
        return conversation
    
    def list_conversations(self, model_filter: Optional[str] = None, limit: Optional[int] = None) -> List[Tuple[str, str, datetime]]:
        """
        List conversations with basic metadata.
        
        Args:
            model_filter: Optional model name filter
            limit: Optional limit on number of results
            
        Returns:
            List of tuples: (conversation_id, title, updated_at)
        """
        conn = self._get_connection()
        
        query = "SELECT conversation_id, title, updated_at FROM conversations"
        params = []
        
        if model_filter:
            query += " WHERE model_name = ?"
            params.append(model_filter)
        
        query += " ORDER BY updated_at DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        cursor = conn.execute(query, params)
        conversations = [
            (row['conversation_id'], row['title'], datetime.fromisoformat(row['updated_at']))
            for row in cursor.fetchall()
        ]
        
        logger.debug(f"Listed {len(conversations)} conversations from database")
        return conversations
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation from the database.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            True if deleted, False if not found
        """
        with self.transaction() as conn:
            cursor = conn.execute("DELETE FROM conversations WHERE conversation_id = ?", (conversation_id,))
            deleted = cursor.rowcount > 0
        
        if deleted:
            logger.debug(f"Deleted conversation from database: {conversation_id}")
        
        return deleted
    
    def clear_all_conversations(self) -> int:
        """
        Clear all conversations and messages from the database.
        
        Returns:
            Number of conversations deleted
        """
        with self.transaction() as conn:
            # Count conversations before deletion
            cursor = conn.execute("SELECT COUNT(*) FROM conversations")
            count = cursor.fetchone()[0]
            
            # Delete all messages first (due to foreign key constraints)
            conn.execute("DELETE FROM messages")
            
            # Delete all conversations
            conn.execute("DELETE FROM conversations")
        
        logger.info(f"Cleared all conversation history: {count} conversations deleted")
        return count
    
    def _save_message(self, conn: sqlite3.Connection, message: ChatMessage, conversation_id: str, sequence: int) -> None:
        """Save a message to the database."""
        message_id = message.message_id or f"{conversation_id}_msg_{sequence}"
        
        conn.execute("""
            INSERT OR REPLACE INTO messages (
                message_id, conversation_id, role, content,
                model_name, tokens_used, generation_time, timestamp,
                error, is_error, sequence_number
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            message_id,
            conversation_id,
            message.role.value,
            message.content,
            message.model_name,
            message.tokens_used,
            message.generation_time,
            message.timestamp.isoformat(),
            message.error,
            message.is_error,
            sequence
        ))
        
        # Save attachments (images, etc.)
        for i, image in enumerate(message.images):
            attachment_id = f"{message_id}_img_{i}"
            conn.execute("""
                INSERT OR REPLACE INTO message_attachments (
                    attachment_id, message_id, attachment_type,
                    data, filename, mime_type, size
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                attachment_id,
                message_id,
                'image',
                image.data,
                image.filename,
                image.mime_type,
                image.size
            ))
    
    def _row_to_message(self, row: sqlite3.Row) -> ChatMessage:
        """Convert database row to ChatMessage instance."""
        from llamalot.models.chat import MessageRole, ChatImage
        
        # Get attachments
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT * FROM message_attachments WHERE message_id = ?",
            (row['message_id'],)
        )
        
        images = []
        for att_row in cursor.fetchall():
            if att_row['attachment_type'] == 'image':
                image = ChatImage(
                    data=att_row['data'],
                    filename=att_row['filename'],
                    mime_type=att_row['mime_type'],
                    size=att_row['size']
                )
                images.append(image)
        
        return ChatMessage(
            role=MessageRole(row['role']),
            content=row['content'],
            timestamp=datetime.fromisoformat(row['timestamp']),
            images=images,
            message_id=row['message_id'],
            model_name=row['model_name'],
            tokens_used=row['tokens_used'],
            generation_time=row['generation_time'],
            error=row['error'],
            is_error=bool(row['is_error'])
        )
    
    # Application state methods
    def set_app_state(self, key: str, value: Any, description: Optional[str] = None) -> None:
        """
        Set application state value.
        
        Args:
            key: State key
            value: State value (will be serialized as needed)
            description: Optional description
        """
        import json
        
        # Determine value type and serialize
        if isinstance(value, bool):
            value_str = str(value).lower()
            value_type = 'bool'
        elif isinstance(value, int):
            value_str = str(value)
            value_type = 'int'
        elif isinstance(value, float):
            value_str = str(value)
            value_type = 'float'
        elif isinstance(value, (dict, list)):
            value_str = json.dumps(value)
            value_type = 'json'
        else:
            value_str = str(value)
            value_type = 'string'
        
        with self.transaction() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO app_state (key, value, value_type, description, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (key, value_str, value_type, description))
        
        logger.debug(f"Set app state: {key} = {value}")
    
    def get_app_state(self, key: str, default: Any = None) -> Any:
        """
        Get application state value.
        
        Args:
            key: State key
            default: Default value if key not found
            
        Returns:
            State value or default
        """
        import json
        
        conn = self._get_connection()
        cursor = conn.execute("SELECT value, value_type FROM app_state WHERE key = ?", (key,))
        row = cursor.fetchone()
        
        if not row:
            return default
        
        value_str = row['value']
        value_type = row['value_type']
        
        # Deserialize based on type
        try:
            if value_type == 'bool':
                return value_str.lower() == 'true'
            elif value_type == 'int':
                return int(value_str)
            elif value_type == 'float':
                return float(value_str)
            elif value_type == 'json':
                return json.loads(value_str)
            else:
                return value_str
        except (ValueError, json.JSONDecodeError) as e:
            logger.error(f"Failed to deserialize app state {key}: {e}")
            return default
    
    def delete_app_state(self, key: str) -> bool:
        """
        Delete application state value.
        
        Args:
            key: State key
            
        Returns:
            True if deleted, False if not found
        """
        with self.transaction() as conn:
            cursor = conn.execute("DELETE FROM app_state WHERE key = ?", (key,))
            deleted = cursor.rowcount > 0
        
        if deleted:
            logger.debug(f"Deleted app state: {key}")
        
        return deleted
    
    # Utility methods
    def cleanup_old_data(self, days: int = 30) -> Dict[str, int]:
        """
        Clean up old data from the database.
        
        Args:
            days: Number of days to keep data
            
        Returns:
            Dictionary with cleanup statistics
        """
        cutoff_date = datetime.now().timestamp() - (days * 24 * 3600)
        stats = {'models': 0, 'conversations': 0}
        
        with self.transaction() as conn:
            # Clean up old conversations
            cursor = conn.execute("""
                DELETE FROM conversations 
                WHERE updated_at < datetime(?, 'unixepoch')
            """, (cutoff_date,))
            stats['conversations'] = cursor.rowcount
            
            # Clean up unused models (not accessed recently)
            cursor = conn.execute("""
                DELETE FROM models 
                WHERE last_accessed < datetime(?, 'unixepoch')
                AND name NOT IN (SELECT DISTINCT model_name FROM conversations WHERE model_name IS NOT NULL)
            """, (cutoff_date,))
            stats['models'] = cursor.rowcount
        
        logger.info(f"Cleanup completed: {stats}")
        return stats
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with database statistics
        """
        conn = self._get_connection()
        
        stats = {}
        
        # Table row counts
        for table in ['models', 'conversations', 'messages', 'message_attachments', 'app_state']:
            cursor = conn.execute(f"SELECT COUNT(*) as count FROM {table}")
            stats[f"{table}_count"] = cursor.fetchone()['count']
        
        # Database file size
        stats['file_size'] = self.db_path.stat().st_size if self.db_path.exists() else 0
        
        # Schema version
        stats['schema_version'] = self._get_schema_version()
        
        return stats
    
    def close(self) -> None:
        """Close all database connections."""
        with self._lock:
            # Close all connections in the pool, handling thread safety
            current_thread_id = threading.get_ident()
            closed_count = 0
            skipped_count = 0
            
            for thread_id, conn in list(self._connection_pool.items()):
                try:
                    if thread_id == current_thread_id:
                        # Only close connections created in the current thread
                        conn.close()
                        closed_count += 1
                        logger.debug(f"Closed database connection for current thread {thread_id}")
                    else:
                        # Skip connections from other threads - they'll be cleaned up automatically
                        skipped_count += 1
                        logger.debug(f"Skipped closing connection from different thread {thread_id}")
                except Exception as e:
                    logger.debug(f"Error closing connection for thread {thread_id}: {e}")
                    
            self._connection_pool.clear()
        
        logger.info(f"Database connections closed: {closed_count} closed, {skipped_count} skipped (different threads)")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_database_manager(db_path: Optional[Path] = None) -> DatabaseManager:
    """
    Get the global database manager instance.
    
    Args:
        db_path: Optional custom database path
        
    Returns:
        DatabaseManager instance
    """
    global _db_manager
    
    if _db_manager is None:
        if db_path is None:
            from llamalot.backend.config import get_config
            config = get_config()
            db_path = Path(config.database_file) if config.database_file else Path.home() / ".llamalot" / "llamalot.db"
        
        _db_manager = DatabaseManager(db_path)
    
    return _db_manager
