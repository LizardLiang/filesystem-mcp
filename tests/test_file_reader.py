import os
import tempfile
from pathlib import Path
import pytest

from spiderfs_mcp.file.reader import FileReader, LineRange


@pytest.fixture
def reader():
    return FileReader()


def create_test_file(content: str, encoding: str = "utf-8") -> str:
    """Helper to create test files with specified encoding"""
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as temp_file:
        try:
            temp_file.write(content.encode(encoding, errors="surrogateescape"))
        except UnicodeEncodeError:
            # Fallback to surrogateescape for problematic characters
            temp_file.write(content.encode("utf-8", errors="replace"))
        return temp_file.name


class TestFileReader:
    def test_read_file_default_utf8(self, reader):
        content = "Hello, 世界!\nMultiple lines here."
        file_path = create_test_file(content)
        result = reader.read_file(file_path)
        assert result.replace("\r\n", "\n") == content
        os.unlink(file_path)

    def test_read_file_specific_encoding(self, reader):
        content = "Hello in latin1: éàè\n"
        file_path = create_test_file(content, "latin1")
        result = reader.read_file(file_path, "latin1")
        assert result.replace("\r\n", "\n") == content
        os.unlink(file_path)

    def test_read_file_line_range(self, reader):
        content = "Line 1\nLine 2\nLine 3\nLine 4\n"
        file_path = create_test_file(content)
        lines = reader.read_line_range(file_path, LineRange(2, 3))
        assert lines.content == "Line 2\nLine 3\n"
        os.unlink(file_path)

    def test_read_file_invalid_encoding(self, reader):
        content = "Hello, 世界!"
        file_path = create_test_file(content, "utf-8")
        with pytest.raises(UnicodeDecodeError):
            reader.read_file(file_path, "ascii")
        os.unlink(file_path)

    def test_read_file_invalid_line_range(self, reader):
        content = "Line 1\nLine 2\n"
        file_path = create_test_file(content)
        read_result = reader.read_line_range(
            file_path, LineRange(3, 1)
        )  # Invalid range
        assert read_result.error == "End line must be >= start line"
        os.unlink(file_path)

    def test_detect_encoding(self, reader):
        # Test UTF-8 detection
        content = "Hello, 世界!"
        file_path = create_test_file(content, "utf-8")
        assert reader.detect_encoding(file_path) == "utf-8"
        os.unlink(file_path)

        # Test fallback to latin1
        content = "Special chars: éàè"
        file_path = create_test_file(content, "latin1")
        assert reader.detect_encoding(file_path) == "latin1"
        os.unlink(file_path)

    def test_read_file_error_handling(self, reader):
        # Test with problematic content but proper handling
        content = "Normal text\nProblematic: \ud800\nMore text"
        file_path = create_test_file(content)

        # Should not raise an error with proper encoding handling
        result = reader.read_file(file_path)
        assert "Normal text" in result
        os.unlink(file_path)
