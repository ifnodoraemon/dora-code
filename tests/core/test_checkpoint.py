"""Comprehensive tests for checkpoint.py"""
import pytest
from pathlib import Path
from src.core.checkpoint import FileSnapshot, Checkpoint, CheckpointConfig


class TestFileSnapshot:
    """Tests for FileSnapshot."""

    def test_creation_existing_file(self):
        """Test creating snapshot for existing file."""
        snapshot = FileSnapshot(
            path="/test/file.py",
            content="print('hello')",
            exists=True,
            size=14,
            mtime=1234567890.0
        )
        assert snapshot.path == "/test/file.py"
        assert snapshot.content == "print('hello')"
        assert snapshot.exists is True
        assert snapshot.size == 14
        assert snapshot.mtime == 1234567890.0

    def test_creation_nonexistent_file(self):
        """Test creating snapshot for non-existent file."""
        snapshot = FileSnapshot(
            path="/test/missing.py",
            content=None,
            exists=False,
            size=0,
            mtime=None
        )
        assert snapshot.path == "/test/missing.py"
        assert snapshot.content is None
        assert snapshot.exists is False
        assert snapshot.size == 0
        assert snapshot.mtime is None

    def test_to_dict(self):
        """Test converting snapshot to dictionary."""
        snapshot = FileSnapshot(
            path="/test/file.py",
            content="content",
            exists=True,
            size=7,
            mtime=1234567890.0
        )
        data = snapshot.to_dict()
        assert data["path"] == "/test/file.py"
        assert data["content"] == "content"
        assert data["exists"] is True
        assert data["size"] == 7
        assert data["mtime"] == 1234567890.0

    def test_from_dict(self):
        """Test creating snapshot from dictionary."""
        data = {
            "path": "/test/restored.py",
            "content": "restored content",
            "exists": True,
            "size": 16,
            "mtime": 1234567890.0
        }
        snapshot = FileSnapshot.from_dict(data)
        assert snapshot.path == "/test/restored.py"
        assert snapshot.content == "restored content"
        assert snapshot.exists is True
        assert snapshot.size == 16

    def test_from_dict_with_defaults(self):
        """Test from_dict with missing optional fields."""
        data = {"path": "/test/minimal.py"}
        snapshot = FileSnapshot.from_dict(data)
        assert snapshot.path == "/test/minimal.py"
        assert snapshot.content is None
        assert snapshot.exists is True  # Default
        assert snapshot.size == 0  # Default

    def test_roundtrip_to_dict_from_dict(self):
        """Test that to_dict and from_dict are inverses."""
        original = FileSnapshot(
            path="/test/roundtrip.py",
            content="test content",
            exists=True,
            size=12,
            mtime=1234567890.0
        )
        data = original.to_dict()
        restored = FileSnapshot.from_dict(data)
        assert restored.path == original.path
        assert restored.content == original.content
        assert restored.exists == original.exists
        assert restored.size == original.size
        assert restored.mtime == original.mtime


class TestCheckpoint:
    """Tests for Checkpoint."""

    def test_creation_basic(self):
        """Test creating a basic checkpoint."""
        checkpoint = Checkpoint(
            id="cp_123",
            created_at=1234567890.0,
            prompt="Test prompt"
        )
        assert checkpoint.id == "cp_123"
        assert checkpoint.created_at == 1234567890.0
        assert checkpoint.prompt == "Test prompt"
        assert checkpoint.files == []
        assert checkpoint.message_count == 0
        assert checkpoint.description == ""

    def test_creation_with_files(self):
        """Test creating checkpoint with file snapshots."""
        snapshot1 = FileSnapshot(
            path="/test/file1.py",
            content="content1",
            exists=True,
            size=8,
            mtime=None
        )
        snapshot2 = FileSnapshot(
            path="/test/file2.py",
            content="content2",
            exists=True,
            size=8,
            mtime=None
        )
        checkpoint = Checkpoint(
            id="cp_456",
            created_at=1234567890.0,
            prompt="Multi-file edit",
            files=[snapshot1, snapshot2],
            message_count=5,
            description="Edited two files"
        )
        assert len(checkpoint.files) == 2
        assert checkpoint.message_count == 5
        assert checkpoint.description == "Edited two files"

    def test_to_dict(self):
        """Test converting checkpoint to dictionary."""
        snapshot = FileSnapshot(
            path="/test/file.py",
            content="content",
            exists=True,
            size=7,
            mtime=None
        )
        checkpoint = Checkpoint(
            id="cp_789",
            created_at=1234567890.0,
            prompt="Test",
            files=[snapshot],
            message_count=3
        )
        data = checkpoint.to_dict()
        assert data["id"] == "cp_789"
        assert data["created_at"] == 1234567890.0
        assert data["prompt"] == "Test"
        assert len(data["files"]) == 1
        assert data["message_count"] == 3

    def test_from_dict(self):
        """Test creating checkpoint from dictionary."""
        data = {
            "id": "cp_from_dict",
            "created_at": 1234567890.0,
            "prompt": "Restored prompt",
            "files": [
                {
                    "path": "/test/file.py",
                    "content": "content",
                    "exists": True,
                    "size": 7,
                    "mtime": None
                }
            ],
            "message_count": 10,
            "description": "Restored checkpoint"
        }
        checkpoint = Checkpoint.from_dict(data)
        assert checkpoint.id == "cp_from_dict"
        assert checkpoint.prompt == "Restored prompt"
        assert len(checkpoint.files) == 1
        assert checkpoint.files[0].path == "/test/file.py"
        assert checkpoint.message_count == 10

    def test_from_dict_with_defaults(self):
        """Test from_dict with missing optional fields."""
        data = {
            "id": "cp_minimal",
            "created_at": 1234567890.0
        }
        checkpoint = Checkpoint.from_dict(data)
        assert checkpoint.id == "cp_minimal"
        assert checkpoint.prompt == ""  # Default
        assert checkpoint.files == []
        assert checkpoint.message_count == 0

    def test_from_dict_empty_files(self):
        """Test from_dict with empty files list."""
        data = {
            "id": "cp_no_files",
            "created_at": 1234567890.0,
            "prompt": "No files",
            "files": []
        }
        checkpoint = Checkpoint.from_dict(data)
        assert checkpoint.files == []

    def test_roundtrip_to_dict_from_dict(self):
        """Test that to_dict and from_dict are inverses."""
        snapshot = FileSnapshot(
            path="/test/roundtrip.py",
            content="test",
            exists=True,
            size=4,
            mtime=1234567890.0
        )
        original = Checkpoint(
            id="cp_roundtrip",
            created_at=1234567890.0,
            prompt="Roundtrip test",
            files=[snapshot],
            message_count=7,
            description="Test description"
        )
        data = original.to_dict()
        restored = Checkpoint.from_dict(data)
        assert restored.id == original.id
        assert restored.created_at == original.created_at
        assert restored.prompt == original.prompt
        assert len(restored.files) == len(original.files)
        assert restored.files[0].path == original.files[0].path
        assert restored.message_count == original.message_count


class TestCheckpointConfig:
    """Tests for CheckpointConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = CheckpointConfig()
        assert config.enabled is True
        assert config.save_directory == ".doraemon/checkpoints"
        assert config.max_file_size == 1024 * 1024  # 1MB
        assert config.retention_days == 30
        assert config.compress is True

    def test_custom_values(self):
        """Test creating config with custom values."""
        config = CheckpointConfig(
            enabled=False,
            save_directory="/custom/path",
            max_file_size=2048 * 1024,  # 2MB
            retention_days=60,
            compress=False
        )
        assert config.enabled is False
        assert config.save_directory == "/custom/path"
        assert config.max_file_size == 2048 * 1024
        assert config.retention_days == 60
        assert config.compress is False

    def test_partial_custom_values(self):
        """Test creating config with some custom values."""
        config = CheckpointConfig(
            retention_days=90,
            compress=False
        )
        assert config.enabled is True  # Default
        assert config.retention_days == 90  # Custom
        assert config.compress is False  # Custom
        assert config.max_file_size == 1024 * 1024  # Default
