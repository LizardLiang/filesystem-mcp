import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from unittest.mock import patch, MagicMock
from spiderfs_mcp.server import app
from spiderfs_mcp.file.writer import FileWriteResult


client = TestClient(app)


@pytest.fixture
def mock_path_exists():
    with patch.object(Path, "exists") as mock_exists:
        mock_exists.return_value = True
        yield mock_exists


@pytest.fixture
def mock_path_is_file():
    with patch.object(Path, "is_file") as mock_is_file:
        mock_is_file.return_value = True
        yield mock_is_file


def test_apply_line_edits_success(mock_path_exists, mock_path_is_file):
    with patch("spiderfs_mcp.file.writer.FileWriter.apply_line_edits") as mock_apply:
        # Mock successful line edit
        mock_apply.return_value = FileWriteResult(
            success=True,
            changed_lines=2,
            backup_path="test.txt.bak",
            metadata={"test": "value"}
        )
        
        response = client.post(
            "/api/v1/file/write/lines",
            json={
                "path": "test.txt",
                "edits": [
                    {
                        "line_start": 2,
                        "line_end": 3,
                        "new_content": "replacement content"
                    }
                ],
                "create_backup": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["changed_lines"] == 2
        assert data["backup_path"] == "test.txt.bak"
        assert data["metadata"]["test"] == "value"


def test_apply_line_edits_validation_error():
    response = client.post(
        "/api/v1/file/write/lines",
        json={
            "path": "test.txt",
            "edits": [
                {
                    "line_start": 3,
                    "line_end": 2,  # Invalid: end < start
                    "new_content": "replacement content"
                }
            ]
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_apply_line_edits_file_not_found():
    with patch.object(Path, "exists") as mock_exists:
        mock_exists.return_value = False
        
        response = client.post(
            "/api/v1/file/write/lines",
            json={
                "path": "nonexistent.txt",
                "edits": [
                    {
                        "line_start": 1,
                        "line_end": 1,
                        "new_content": "replacement content"
                    }
                ]
            }
        )
        
        assert response.status_code == 404


def test_apply_line_edits_writer_error(mock_path_exists, mock_path_is_file):
    with patch("spiderfs_mcp.file.writer.FileWriter.apply_line_edits") as mock_apply:
        # Mock writer error
        mock_apply.return_value = FileWriteResult(
            success=False,
            error="Test writer error"
        )
        
        response = client.post(
            "/api/v1/file/write/lines",
            json={
                "path": "test.txt",
                "edits": [
                    {
                        "line_start": 1,
                        "line_end": 1,
                        "new_content": "replacement content"
                    }
                ]
            }
        )
        
        assert response.status_code == 400
        assert response.json()["detail"] == "Test writer error"


def test_replace_string_success(mock_path_exists, mock_path_is_file):
    with patch("spiderfs_mcp.file.writer.FileWriter.replace_string") as mock_replace:
        # Mock successful string replacement
        mock_replace.return_value = FileWriteResult(
            success=True,
            changed_lines=5,
            backup_path="test.txt.bak",
            metadata={"replacements": 10}
        )
        
        response = client.post(
            "/api/v1/file/write/replace",
            json={
                "path": "test.txt",
                "old_string": "find",
                "new_string": "replace",
                "max_replacements": 0,
                "create_backup": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["changed_lines"] == 5
        assert data["backup_path"] == "test.txt.bak"
        assert data["metadata"]["replacements"] == 10


def test_replace_string_validation_error():
    response = client.post(
        "/api/v1/file/write/replace",
        json={
            "path": "test.txt",
            "old_string": "",  # Invalid: empty string
            "new_string": "replacement"
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_replace_string_file_not_found():
    with patch.object(Path, "exists") as mock_exists:
        mock_exists.return_value = False
        
        response = client.post(
            "/api/v1/file/write/replace",
            json={
                "path": "nonexistent.txt",
                "old_string": "find",
                "new_string": "replace"
            }
        )
        
        assert response.status_code == 404


def test_replace_string_writer_error(mock_path_exists, mock_path_is_file):
    with patch("spiderfs_mcp.file.writer.FileWriter.replace_string") as mock_replace:
        # Mock writer error
        mock_replace.return_value = FileWriteResult(
            success=False,
            error="Test replace error"
        )
        
        response = client.post(
            "/api/v1/file/write/replace",
            json={
                "path": "test.txt",
                "old_string": "find",
                "new_string": "replace"
            }
        )
        
        assert response.status_code == 400
        assert response.json()["detail"] == "Test replace error"