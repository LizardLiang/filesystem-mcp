import pytest
from unittest.mock import patch, Mock
from pathlib import Path
from spiderfs_mcp.search.ripgrep import RipgrepSearch, SearchMatch, SearchResult


def test_ripgrep_empty_lines():
    with patch('subprocess.run') as mock_run:
        # Mock ripgrep output with empty lines
        mock_run.return_value = Mock(
            returncode=0,
            stdout="\nfile.txt:1:valid line\n\n",
            stderr=""
        )
        
        search = RipgrepSearch()
        result = search.search("pattern", "file.txt")
        
        assert len(result.matches) == 1
        assert result.matches[0].line_content == "valid line"


def test_ripgrep_malformed_output():
    with patch('subprocess.run') as mock_run:
        # Mock ripgrep output with malformed line
        mock_run.return_value = Mock(
            returncode=0,
            stdout="malformed_line_without_proper_format\nfile.txt:1:valid line",
            stderr=""
        )
        
        search = RipgrepSearch()
        result = search.search("pattern", "file.txt")
        
        # Should only get the valid line
        assert len(result.matches) == 1
        assert result.matches[0].line_content == "valid line"


def test_ripgrep_search_success():
    with patch('subprocess.run') as mock_run:
        # Mock successful ripgrep output
        mock_run.return_value = Mock(
            returncode=0,
            stdout="file.txt:1:hello world\nfile.txt:2:hello again\n",
            stderr=""
        )
        
        search = RipgrepSearch()
        result = search.search("hello", "file.txt")
        
        assert len(result.matches) == 2
        assert result.error is None
        assert result.matches[0].line_number == 1
        assert result.matches[0].line_content == "hello world"
        assert result.matches[0].path == "file.txt"


def test_ripgrep_search_no_matches():
    with patch('subprocess.run') as mock_run:
        # Mock ripgrep output with no matches
        mock_run.return_value = Mock(
            returncode=1,  # ripgrep returns 1 when no matches found
            stdout="",
            stderr=""
        )
        
        search = RipgrepSearch()
        result = search.search("notfound", "file.txt")
        
        assert len(result.matches) == 0
        assert result.error is None


def test_ripgrep_search_error():
    with patch('subprocess.run') as mock_run:
        # Mock ripgrep error
        mock_run.return_value = Mock(
            returncode=2,
            stdout="",
            stderr="some error occurred"
        )
        
        search = RipgrepSearch()
        result = search.search("pattern", "file.txt")
        
        assert len(result.matches) == 0
        assert result.error == "ripgrep error: some error occurred"


def test_ripgrep_subprocess_exception():
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = Exception("Mock subprocess failure")
        
        search = RipgrepSearch()
        result = search.search("pattern", "file.txt")
        
        assert len(result.matches) == 0
        assert "Search failed: Mock subprocess failure" in result.error


def test_ripgrep_max_matches():
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(
            returncode=0,
            stdout="file.txt:1:line1\nfile.txt:2:line2\nfile.txt:3:line3",
            stderr=""
        )
        
        search = RipgrepSearch()
        result = search.search("pattern", "file.txt", max_matches=2)
        
        # Verify -m 2 was passed to ripgrep
        cmd_args = mock_run.call_args[0][0]
        assert "-m" in cmd_args
        assert "2" in cmd_args
        assert len(result.matches) == 3  # All matches are returned