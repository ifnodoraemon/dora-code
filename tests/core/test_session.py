"""Comprehensive tests for session.py"""
import pytest
import time
from pathlib import Path
from src.core.session import SessionMetadata, SessionData


class TestSessionMetadata:
    """Tests for SessionMetadata."""

    def test_creation_with_defaults(self):
        """Test creating session metadata with defaults."""
        metadata = SessionMetadata(id="test_123")
        assert metadata.id == "test_123"
        assert metadata.name is None
        assert metadata.project == "default"
        assert metadata.message_count == 0
        assert metadata.mode == "build"
        assert metadata.parent_id is None
        assert metadata.tags == []

    def test_creation_with_all_fields(self):
        """Test creating session metadata with all fields."""
        metadata = SessionMetadata(
            id="session_456",
            name="My Session",
            project="myproject",
            message_count=10,
            total_tokens=5000,
            mode="plan",
            parent_id="parent_123",
            tags=["important", "test"],
            description="Test session"
        )
        assert metadata.name == "My Session"
        assert metadata.project == "myproject"
        assert metadata.message_count == 10
        assert metadata.mode == "plan"
        assert metadata.parent_id == "parent_123"
        assert len(metadata.tags) == 2

    def test_to_dict(self):
        """Test converting metadata to dictionary."""
        metadata = SessionMetadata(
            id="test_789",
            name="Test",
            project="proj",
            message_count=5
        )
        data = metadata.to_dict()
        assert data["id"] == "test_789"
        assert data["name"] == "Test"
        assert data["project"] == "proj"
        assert data["message_count"] == 5
        assert "created_at" in data
        assert "updated_at" in data

    def test_from_dict_basic(self):
        """Test creating metadata from dictionary."""
        data = {
            "id": "from_dict_123",
            "name": "From Dict",
            "project": "test_project",
            "message_count": 15
        }
        metadata = SessionMetadata.from_dict(data)
        assert metadata.id == "from_dict_123"
        assert metadata.name == "From Dict"
        assert metadata.project == "test_project"
        assert metadata.message_count == 15

    def test_from_dict_with_defaults(self):
        """Test from_dict with missing optional fields."""
        data = {"id": "minimal_123"}
        metadata = SessionMetadata.from_dict(data)
        assert metadata.id == "minimal_123"
        assert metadata.project == "default"
        assert metadata.mode == "build"
        assert metadata.tags == []

    def test_from_dict_with_all_fields(self):
        """Test from_dict with all fields."""
        data = {
            "id": "full_123",
            "name": "Full Session",
            "project": "full_project",
            "created_at": 1234567890.0,
            "updated_at": 1234567900.0,
            "message_count": 20,
            "total_tokens": 10000,
            "mode": "plan",
            "parent_id": "parent_456",
            "tags": ["tag1", "tag2"],
            "description": "Full description"
        }
        metadata = SessionMetadata.from_dict(data)
        assert metadata.name == "Full Session"
        assert metadata.created_at == 1234567890.0
        assert metadata.updated_at == 1234567900.0
        assert metadata.total_tokens == 10000
        assert metadata.parent_id == "parent_456"
        assert metadata.description == "Full description"

    def test_get_display_name_with_name(self):
        """Test display name when name is set."""
        metadata = SessionMetadata(id="test_123", name="My Custom Name")
        assert metadata.get_display_name() == "My Custom Name"

    def test_get_display_name_without_name(self):
        """Test display name when name is not set."""
        metadata = SessionMetadata(id="test_123456789")
        display_name = metadata.get_display_name()
        assert "test_123" in display_name  # Should include ID prefix
        assert "Session" in display_name

    def test_timestamps_auto_generated(self):
        """Test that timestamps are auto-generated."""
        before = time.time()
        metadata = SessionMetadata(id="test_123")
        after = time.time()
        assert before <= metadata.created_at <= after
        assert before <= metadata.updated_at <= after


class TestSessionData:
    """Tests for SessionData."""

    def test_creation_with_defaults(self):
        """Test creating session data with defaults."""
        metadata = SessionMetadata(id="test_123")
        session = SessionData(metadata=metadata)
        assert session.metadata.id == "test_123"
        assert session.messages == []
        assert session.summaries == []
        assert session.checkpoints == []

    def test_creation_with_data(self):
        """Test creating session data with messages and summaries."""
        metadata = SessionMetadata(id="test_456")
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"}
        ]
        summaries = [{"content": "Summary", "message_count": 2}]
        checkpoints = ["checkpoint_1", "checkpoint_2"]

        session = SessionData(
            metadata=metadata,
            messages=messages,
            summaries=summaries,
            checkpoints=checkpoints
        )
        assert len(session.messages) == 2
        assert len(session.summaries) == 1
        assert len(session.checkpoints) == 2

    def test_to_dict(self):
        """Test converting session data to dictionary."""
        metadata = SessionMetadata(id="test_789", name="Test Session")
        messages = [{"role": "user", "content": "Test"}]
        session = SessionData(metadata=metadata, messages=messages)

        data = session.to_dict()
        assert data["version"] == 1
        assert data["metadata"]["id"] == "test_789"
        assert len(data["messages"]) == 1
        assert "summaries" in data
        assert "checkpoints" in data

    def test_from_dict_basic(self):
        """Test creating session data from dictionary."""
        data = {
            "version": 1,
            "metadata": {"id": "from_dict_123", "name": "Test"},
            "messages": [{"role": "user", "content": "Hello"}],
            "summaries": [],
            "checkpoints": []
        }
        session = SessionData.from_dict(data)
        assert session.metadata.id == "from_dict_123"
        assert len(session.messages) == 1
        assert session.messages[0]["content"] == "Hello"

    def test_from_dict_with_all_data(self):
        """Test from_dict with complete data."""
        data = {
            "version": 1,
            "metadata": {
                "id": "full_123",
                "name": "Full Session",
                "message_count": 5,
                "tags": ["test"]
            },
            "messages": [
                {"role": "user", "content": "Message 1"},
                {"role": "assistant", "content": "Response 1"}
            ],
            "summaries": [
                {"content": "Summary 1", "message_count": 2}
            ],
            "checkpoints": ["cp_1", "cp_2", "cp_3"]
        }
        session = SessionData.from_dict(data)
        assert session.metadata.name == "Full Session"
        assert len(session.messages) == 2
        assert len(session.summaries) == 1
        assert len(session.checkpoints) == 3

    def test_from_dict_with_missing_fields(self):
        """Test from_dict with missing optional fields."""
        data = {
            "metadata": {"id": "minimal_123"}
        }
        session = SessionData.from_dict(data)
        assert session.metadata.id == "minimal_123"
        assert session.messages == []
        assert session.summaries == []
        assert session.checkpoints == []

    def test_roundtrip_to_dict_from_dict(self):
        """Test that to_dict and from_dict are inverses."""
        metadata = SessionMetadata(
            id="roundtrip_123",
            name="Roundtrip Test",
            message_count=10
        )
        messages = [
            {"role": "user", "content": "Test message"},
            {"role": "assistant", "content": "Test response"}
        ]
        original = SessionData(metadata=metadata, messages=messages)

        # Convert to dict and back
        data = original.to_dict()
        restored = SessionData.from_dict(data)

        assert restored.metadata.id == original.metadata.id
        assert restored.metadata.name == original.metadata.name
        assert len(restored.messages) == len(original.messages)
        assert restored.messages[0]["content"] == original.messages[0]["content"]
