import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
from spiderfs_mcp.search.python_search import PythonSearch


def test_python_search_success():
    file_content = "hello world\nhello again\nbye\n"
    with patch("builtins.open", mock_open(read_data=file_content)):
        search = PythonSearch()
        result = search.search_file("hello", "test.txt")
        
        assert len(result.matches) == 2
        assert result.error is None
        assert result.matches[0].line_number == 1
        assert result.matches[0].line_content == "hello world"
        assert result.matches[1].line_number == 2
        assert result.matches[1].line_content == "hello again"


def test_python_search_no_matches():
    file_content = "line1\nline2\nline3\n"
    with patch("builtins.open", mock_open(read_data=file_content)):
        search = PythonSearch()
        result = search.search_file("notfound", "test.txt")
        
        assert len(result.matches) == 0
        assert result.error is None


def test_python_search_max_matches():
    file_content = "match1\nmatch2\nmatch3\n"
    with patch("builtins.open", mock_open(read_data=file_content)):
        search = PythonSearch()
        result = search.search_file("match", "test.txt", max_matches=2)
        
        assert len(result.matches) == 2
        assert result.matches[0].line_number == 1
        assert result.matches[1].line_number == 2


def test_python_search_file_error():
    with patch("builtins.open", side_effect=IOError("file not found")):
        search = PythonSearch()
        result = search.search_file("pattern", "nonexistent.txt")
        
        assert len(result.matches) == 0
        assert result.error == "Search failed: file not found"


def test_python_search_invalid_regex():
    file_content = "test content\n"
    with patch("builtins.open", mock_open(read_data=file_content)):
        search = PythonSearch()
        result = search.search_file("[invalid regex", "test.txt")
        
        assert len(result.matches) == 0
        assert "Search failed" in result.error