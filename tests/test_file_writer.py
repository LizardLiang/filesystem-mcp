import pytest
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path
import os
import tempfile
import shutil
from spiderfs_mcp.file.writer import FileWriter, LineEdit


@pytest.fixture
def temp_file():
    # Create a temporary file for testing
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as f:
        f.write("line 1\nline 2\nline 3\nline 4\nline 5\n")
        temp_path = f.name
    
    yield temp_path
    
    # Clean up
    if os.path.exists(temp_path):
        os.unlink(temp_path)
    
    # Also clean up any backup files
    backup_path = f"{temp_path}.bak"
    if os.path.exists(backup_path):
        os.unlink(backup_path)


def test_apply_line_edits_success(temp_file):
    writer = FileWriter()
    
    # Replace lines 2-3 with new content
    edits = [
        LineEdit(
            line_start=2,
            line_end=3,
            new_content="replacement line 2\nreplacement line 3\n"
        )
    ]
    
    result = writer.apply_line_edits(temp_file, edits)
    
    assert result.success is True
    assert result.changed_lines == 2
    assert result.error is None
    assert result.backup_path is not None
    
    # Verify file contents
    with open(temp_file, 'r') as f:
        content = f.read()
        
    assert content == "line 1\nreplacement line 2\nreplacement line 3\nline 4\nline 5\n"
    
    # Verify backup contents
    with open(result.backup_path, 'r') as f:
        backup_content = f.read()
        
    assert backup_content == "line 1\nline 2\nline 3\nline 4\nline 5\n"


def test_apply_line_edits_multiple(temp_file):
    writer = FileWriter()
    
    # Apply multiple edits
    edits = [
        LineEdit(
            line_start=1,
            line_end=1,
            new_content="new line 1\n"
        ),
        LineEdit(
            line_start=4,
            line_end=5,
            new_content="new line 4\n"
        )
    ]
    
    result = writer.apply_line_edits(temp_file, edits)
    
    assert result.success is True
    
    # Verify file contents
    with open(temp_file, 'r') as f:
        content = f.read()
        
    assert content == "new line 1\nline 2\nline 3\nnew line 4\n"


def test_apply_line_edits_file_not_found():
    writer = FileWriter()
    
    result = writer.apply_line_edits(
        "nonexistent_file.txt",
        [LineEdit(line_start=1, line_end=1, new_content="new content")]
    )
    
    assert result.success is False
    assert "File not found" in result.error


def test_apply_line_edits_invalid_range(temp_file):
    writer = FileWriter()
    
    # Invalid line range (start < 1)
    result = writer.apply_line_edits(
        temp_file,
        [LineEdit(line_start=0, line_end=1, new_content="new content")]
    )
    
    assert result.success is False
    assert "Invalid line number" in result.error
    
    # Invalid line range (end < start)
    result = writer.apply_line_edits(
        temp_file,
        [LineEdit(line_start=3, line_end=2, new_content="new content")]
    )
    
    assert result.success is False
    assert "Invalid line range" in result.error


def test_apply_line_edits_beyond_file_end(temp_file):
    writer = FileWriter()
    
    # Start line beyond file end
    result = writer.apply_line_edits(
        temp_file,
        [LineEdit(line_start=10, line_end=20, new_content="new content")]
    )
    
    assert result.success is False
    assert "beyond the end of file" in result.error


def test_apply_line_edits_no_changes(temp_file):
    writer = FileWriter()
    
    # Read the existing line 2
    with open(temp_file, 'r') as f:
        lines = f.readlines()
        line2 = lines[1]
    
    # Apply an edit that doesn't actually change anything
    result = writer.apply_line_edits(
        temp_file,
        [LineEdit(line_start=2, line_end=2, new_content=line2)]
    )
    
    # Since we're replacing line 2 with exactly the same content,
    # no changes should be made
    assert result.success is True
    assert result.changed_lines == 0
    assert result.metadata is not None
    assert result.metadata.get("unchanged") is True
    assert result.backup_path is None


def test_replace_string_success(temp_file):
    writer = FileWriter()
    
    result = writer.replace_string(temp_file, "line", "CODE")
    
    assert result.success is True
    assert result.error is None
    assert result.backup_path is not None
    
    # Verify file contents
    with open(temp_file, 'r') as f:
        content = f.read()
        
    assert content == "CODE 1\nCODE 2\nCODE 3\nCODE 4\nCODE 5\n"
    
    # Verify metadata
    assert result.metadata is not None
    assert result.metadata.get("replacements") == 5


def test_replace_string_limited_replacements(temp_file):
    writer = FileWriter()
    
    result = writer.replace_string(temp_file, "line", "CODE", max_replacements=2)
    
    assert result.success is True
    
    # Verify file contents
    with open(temp_file, 'r') as f:
        content = f.read()
        
    assert content == "CODE 1\nCODE 2\nline 3\nline 4\nline 5\n"
    
    # Verify metadata
    assert result.metadata is not None
    assert result.metadata.get("replacements") == 2


def test_replace_string_no_match(temp_file):
    writer = FileWriter()
    
    result = writer.replace_string(temp_file, "nonexistent", "replacement")
    
    assert result.success is True
    assert result.changed_lines == 0
    assert result.metadata is not None
    assert result.metadata.get("unchanged") is True
    
    # Verify no backup was kept
    assert result.backup_path is None
    assert not os.path.exists(f"{temp_file}.bak")
    
    # Verify file contents unchanged
    with open(temp_file, 'r') as f:
        content = f.read()
        
    assert content == "line 1\nline 2\nline 3\nline 4\nline 5\n"
