"""
Tests for database management functionality.
"""

import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

from llamalot.backend.database import DatabaseManager, DatabaseError, MigrationError
from llamalot.models import OllamaModel, ChatMessage, ChatConversation
from llamalot.models.ollama_model import ModelDetails, ModelInfo
from llamalot.models.chat import MessageRole


class TestDatabaseManager(unittest.TestCase):
    """Test cases for DatabaseManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        self.db = DatabaseManager(self.db_path)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.db.close()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test database manager initialization."""
        self.assertTrue(self.db_path.exists())
        self.assertEqual(self.db.db_path, self.db_path)
        self.assertEqual(self.db.SCHEMA_VERSION, 1)
    
    def test_schema_creation(self):
        """Test that database schema is created correctly."""
        conn = self.db._get_connection()
        
        # Check that all tables exist
        cursor = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = [
            'app_state', 'conversations', 'db_metadata',
            'message_attachments', 'messages', 'models'
        ]
        self.assertEqual(sorted(tables), sorted(expected_tables))
    
    def test_schema_version(self):
        """Test schema version management."""
        # Initial version should be set to current schema version
        version = self.db._get_schema_version()
        self.assertEqual(version, self.db.SCHEMA_VERSION)
        
        # Test setting version
        self.db._set_schema_version(2)
        version = self.db._get_schema_version()
        self.assertEqual(version, 2)
    
    def test_transaction_context_manager(self):
        """Test transaction context manager."""
        # Test successful transaction
        with self.db.transaction() as conn:
            conn.execute("INSERT INTO app_state (key, value) VALUES ('test', 'value')")
        
        # Verify data was committed
        conn = self.db._get_connection()
        cursor = conn.execute("SELECT value FROM app_state WHERE key = 'test'")
        row = cursor.fetchone()
        self.assertEqual(row['value'], 'value')
        
        # Test failed transaction (should rollback)
        try:
            with self.db.transaction() as conn:
                conn.execute("INSERT INTO app_state (key, value) VALUES ('test2', 'value2')")
                raise ValueError("Test error")
        except ValueError:
            pass
        
        # Verify rollback - test2 should not exist
        cursor = conn.execute("SELECT value FROM app_state WHERE key = 'test2'")
        row = cursor.fetchone()
        self.assertIsNone(row)
    
    def test_model_operations(self):
        """Test model save, get, list, and delete operations."""
        # Create test model
        model = OllamaModel(
            name="test-model:7b",
            size=1000000000,
            digest="abc123",
            modified_at=datetime.now(),
            details=ModelDetails(
                format="gguf",
                family="llama",
                families=["llama"],
                parameter_size="7B",
                quantization_level="Q4_0"
            )
        )
        
        # Test save
        self.db.save_model(model)
        
        # Test get
        retrieved_model = self.db.get_model("test-model:7b")
        self.assertIsNotNone(retrieved_model)
        self.assertEqual(retrieved_model.name, "test-model:7b")
        self.assertEqual(retrieved_model.size, 1000000000)
        self.assertEqual(retrieved_model.details.family, "llama")
        
        # Test get non-existent model
        non_existent = self.db.get_model("non-existent")
        self.assertIsNone(non_existent)
        
        # Test list
        models = self.db.list_models()
        self.assertEqual(len(models), 1)
        self.assertEqual(models[0].name, "test-model:7b")
        
        # Test list with family filter
        filtered_models = self.db.list_models(family_filter="llama")
        self.assertEqual(len(filtered_models), 1)
        
        empty_filter = self.db.list_models(family_filter="gpt")
        self.assertEqual(len(empty_filter), 0)
        
        # Test delete
        deleted = self.db.delete_model("test-model:7b")
        self.assertTrue(deleted)
        
        # Verify deletion
        retrieved_after_delete = self.db.get_model("test-model:7b")
        self.assertIsNone(retrieved_after_delete)
        
        # Test delete non-existent
        deleted_again = self.db.delete_model("test-model:7b")
        self.assertFalse(deleted_again)
    
    def test_model_with_info(self):
        """Test model operations with ModelInfo."""
        model = OllamaModel(
            name="test-model-with-info:7b",
            size=1000000000,
            digest="def456",
            modified_at=datetime.now(),
            details=ModelDetails(family="llama"),
            model_info=ModelInfo(
                architecture="llama",
                parameter_count=7000000000,
                context_length=4096,
                vocab_size=32000
            )
        )
        
        # Save and retrieve
        self.db.save_model(model)
        retrieved = self.db.get_model("test-model-with-info:7b")
        
        self.assertIsNotNone(retrieved)
        self.assertIsNotNone(retrieved.model_info)
        self.assertEqual(retrieved.model_info.architecture, "llama")
        self.assertEqual(retrieved.model_info.parameter_count, 7000000000)
        self.assertEqual(retrieved.model_info.context_length, 4096)
        self.assertEqual(retrieved.model_info.vocab_size, 32000)
    
    def test_conversation_operations(self):
        """Test conversation save, get, list, and delete operations."""
        # First create a test model that the conversation can reference
        test_model = OllamaModel(
            name="test-model:7b",
            size=1000000000,
            digest="abc123",
            modified_at=datetime.now()
        )
        self.db.save_model(test_model)
        
        # Create test conversation
        conversation = ChatConversation(
            conversation_id="test-conv-1",
            title="Test Conversation",
            model_name="test-model:7b",
            system_prompt="You are helpful"
        )
        
        # Add messages
        msg1 = ChatMessage(role=MessageRole.USER, content="Hello")
        msg2 = ChatMessage(role=MessageRole.ASSISTANT, content="Hi there!")
        conversation.add_message(msg1)
        conversation.add_message(msg2)
        
        # Test save
        self.db.save_conversation(conversation)
        
        # Test get
        retrieved = self.db.get_conversation("test-conv-1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.conversation_id, "test-conv-1")
        self.assertEqual(retrieved.title, "Test Conversation")
        self.assertEqual(len(retrieved.messages), 2)
        self.assertEqual(retrieved.messages[0].content, "Hello")
        self.assertEqual(retrieved.messages[1].content, "Hi there!")
        
        # Test get non-existent
        non_existent = self.db.get_conversation("non-existent")
        self.assertIsNone(non_existent)
        
        # Test list
        conversations = self.db.list_conversations()
        self.assertEqual(len(conversations), 1)
        self.assertEqual(conversations[0][0], "test-conv-1")  # conversation_id
        self.assertEqual(conversations[0][1], "Test Conversation")  # title
        
        # Test list with model filter
        filtered = self.db.list_conversations(model_filter="test-model:7b")
        self.assertEqual(len(filtered), 1)
        
        empty_filter = self.db.list_conversations(model_filter="other-model")
        self.assertEqual(len(empty_filter), 0)
        
        # Test list with limit
        limited = self.db.list_conversations(limit=1)
        self.assertEqual(len(limited), 1)
        
        # Test delete
        deleted = self.db.delete_conversation("test-conv-1")
        self.assertTrue(deleted)
        
        # Verify deletion
        retrieved_after_delete = self.db.get_conversation("test-conv-1")
        self.assertIsNone(retrieved_after_delete)
        
        # Test delete non-existent
        deleted_again = self.db.delete_conversation("test-conv-1")
        self.assertFalse(deleted_again)
    
    def test_message_with_images(self):
        """Test saving and retrieving messages with image attachments."""
        # Create model first
        model = OllamaModel(
            name="test-model",
            size=1000,
            digest="test123",
            modified_at=datetime.now()
        )
        self.db.save_model(model)
        
        # Create conversation that references the model
        conv = ChatConversation(
            conversation_id="test-conv",
            title="Test Conversation",
            model_name="test-model"  # Reference the model we created
        )
    
    def test_app_state_operations(self):
        """Test application state operations."""
        # Test setting different types
        self.db.set_app_state("string_key", "string_value")
        self.db.set_app_state("int_key", 42)
        self.db.set_app_state("float_key", 3.14)
        self.db.set_app_state("bool_key", True)
        self.db.set_app_state("json_key", {"nested": "dict", "list": [1, 2, 3]})
        
        # Test getting values
        self.assertEqual(self.db.get_app_state("string_key"), "string_value")
        self.assertEqual(self.db.get_app_state("int_key"), 42)
        self.assertEqual(self.db.get_app_state("float_key"), 3.14)
        self.assertEqual(self.db.get_app_state("bool_key"), True)
        self.assertEqual(self.db.get_app_state("json_key"), {"nested": "dict", "list": [1, 2, 3]})
        
        # Test default values
        self.assertEqual(self.db.get_app_state("non_existent", "default"), "default")
        self.assertIsNone(self.db.get_app_state("non_existent"))
        
        # Test delete
        deleted = self.db.delete_app_state("string_key")
        self.assertTrue(deleted)
        
        # Verify deletion
        self.assertIsNone(self.db.get_app_state("string_key"))
        
        # Test delete non-existent
        deleted_again = self.db.delete_app_state("string_key")
        self.assertFalse(deleted_again)
    
    def test_cleanup_old_data(self):
        """Test cleanup of old data."""
        # Create old model first
        old_model = OllamaModel(
            name="old-model",
            size=1000,
            digest="old123",
            modified_at=datetime.now()
        )
        self.db.save_model(old_model)
        
        # Manually update last_accessed to be old
        conn = self.db._get_connection()
        old_timestamp = (datetime.now() - timedelta(days=31)).isoformat()
        conn.execute(
            "UPDATE models SET last_accessed = ? WHERE name = ?",
            (old_timestamp, "old-model")
        )
        
        # Create old conversation that references the model
        old_conv = ChatConversation(
            conversation_id="old-conv",
            title="Old Conversation",
            model_name="old-model"  # Reference the model we created
        )
        self.db.save_conversation(old_conv)
        
        # Manually update timestamp to be old
        conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE conversation_id = ?",
            (old_timestamp, "old-conv")
        )
        
        # Run cleanup
        stats = self.db.cleanup_old_data(days=30)
        
        # Verify cleanup
        self.assertGreater(stats['models'], 0)
        self.assertGreater(stats['conversations'], 0)
        
        # Verify data was actually removed
        self.assertIsNone(self.db.get_model("old-model"))
        self.assertIsNone(self.db.get_conversation("old-conv"))
    
    def test_database_stats(self):
        """Test database statistics."""
        # Add some data
        model = OllamaModel(
            name="stats-model",
            size=1000,
            digest="stats123",
            modified_at=datetime.now()
        )
        self.db.save_model(model)
        
        conversation = ChatConversation(
            conversation_id="stats-conv",
            title="Stats Conversation"
        )
        conversation.add_message(ChatMessage(role=MessageRole.USER, content="Test"))
        self.db.save_conversation(conversation)
        
        self.db.set_app_state("stats_test", "value")
        
        # Get stats
        stats = self.db.get_database_stats()
        
        # Verify stats
        self.assertIn('models_count', stats)
        self.assertIn('conversations_count', stats)
        self.assertIn('messages_count', stats)
        self.assertIn('app_state_count', stats)
        self.assertIn('file_size', stats)
        self.assertIn('schema_version', stats)
        
        self.assertGreaterEqual(stats['models_count'], 1)
        self.assertGreaterEqual(stats['conversations_count'], 1)
        self.assertGreaterEqual(stats['messages_count'], 1)
        self.assertGreaterEqual(stats['app_state_count'], 1)
        self.assertGreater(stats['file_size'], 0)
        self.assertEqual(stats['schema_version'], 1)
    
    def test_context_manager(self):
        """Test database manager as context manager."""
        with DatabaseManager(self.db_path) as db:
            self.assertIsInstance(db, DatabaseManager)
            # Add some data
            db.set_app_state("context_test", "value")
        
        # Verify data persists after context exit
        new_db = DatabaseManager(self.db_path)
        value = new_db.get_app_state("context_test")
        self.assertEqual(value, "value")
        new_db.close()
    
    def test_thread_safety(self):
        """Test thread-local connections."""
        import threading
        
        results = {}
        
        def worker(thread_id):
            # Each thread should get its own connection
            conn1 = self.db._get_connection()
            conn2 = self.db._get_connection()
            
            # Same thread should get same connection
            results[thread_id] = (conn1 is conn2, id(conn1))
        
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Each thread should have gotten the same connection for multiple calls
        for thread_id, (same_conn, conn_id) in results.items():
            self.assertTrue(same_conn, f"Thread {thread_id} got different connections")
        
        # Different threads should have different connections
        conn_ids = [conn_id for same_conn, conn_id in results.values()]
        self.assertEqual(len(set(conn_ids)), len(conn_ids), "Threads shared connections")


class TestDatabaseMigration(unittest.TestCase):
    """Test cases for database migration functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "migration_test.db"
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_migration_from_empty(self):
        """Test migration from empty database."""
        # Create database manager - should trigger migration
        db = DatabaseManager(self.db_path)
        
        # Verify schema version
        version = db._get_schema_version()
        self.assertEqual(version, db.SCHEMA_VERSION)
        
        # Verify tables exist
        conn = db._get_connection()
        cursor = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='models'
        """)
        self.assertIsNotNone(cursor.fetchone())
        
        db.close()
    
    def test_migration_error_handling(self):
        """Test migration error handling."""
        # Create a database with a newer schema version
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE db_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        conn.execute("INSERT INTO db_metadata (key, value) VALUES ('schema_version', '999')")
        conn.close()
        
        # Should raise MigrationError
        with self.assertRaises(MigrationError):
            DatabaseManager(self.db_path)


class TestDatabaseErrorHandling(unittest.TestCase):
    """Test cases for database error handling."""
    
    def test_database_error_inheritance(self):
        """Test that database errors inherit correctly."""
        self.assertTrue(issubclass(DatabaseError, Exception))
        self.assertTrue(issubclass(MigrationError, DatabaseError))
    
    def test_database_error_creation(self):
        """Test database error creation."""
        error = DatabaseError("Test error")
        self.assertEqual(str(error), "Test error")
        
        migration_error = MigrationError("Migration failed")
        self.assertEqual(str(migration_error), "Migration failed")


if __name__ == '__main__':
    unittest.main()
