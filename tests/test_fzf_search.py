import pytest
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.spiderfs_mcp.search.fzf import FzfSearch

@pytest.fixture
def fzf_search():
    return FzfSearch()

class TestFzfSearch:
    def test_fzf_available_check(self, fzf_search):
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            assert fzf_search._check_fzf_installed() is True

            mock_run.side_effect = FileNotFoundError()
            assert fzf_search._check_fzf_installed() is False

    def test_windows_drive_detection(self, fzf_search):
        with patch('win32api.GetLogicalDriveStrings', return_value='C:\\\0D:\\\0'):
            drives = fzf_search._get_windows_drives()
            assert drives == ['C:\\\\', 'D:\\\\']

        with patch.dict('sys.modules', {'win32api': None}):
            drives = fzf_search._get_windows_drives()
            assert drives == ['C:\\\\']

    def test_prepare_search_paths(self, fzf_search, tmp_path):
        test_path = str(tmp_path)
        assert fzf_search._prepare_search_paths(test_path) == [test_path]

        with patch('platform.system', return_value='Windows'), \
             patch.object(fzf_search, '_get_windows_drives', return_value=['C:\\\\']):
            assert fzf_search._prepare_search_paths() == ['C:\\\\']

        with patch('platform.system', return_value='Linux'):
            assert fzf_search._prepare_search_paths() == ['/']

    def test_python_fallback_search(self, fzf_search, tmp_path):
        test_file1 = tmp_path / "test_file1.txt"
        test_file1.write_text("content")
        test_dir = tmp_path / "subdir"
        test_dir.mkdir()
        test_file2 = test_dir / "test_file2.txt"
        test_file2.write_text("content")

        # Basic test with pattern 'test'
        results = fzf_search._python_fallback_search("test", str(tmp_path), 5)
        assert str(test_file1) in results
        assert str(test_file2) in results

        # Test regex pattern with dot
        results = fzf_search._python_fallback_search("t.st", str(tmp_path), 5)
        assert str(test_file1) in results

        # Test limit
        results = fzf_search._python_fallback_search("test", str(tmp_path), 1)
        assert len(results) == 1

        # Test invalid regex pattern
        results = fzf_search._python_fallback_search("t[est", str(tmp_path), 5)
        assert str(test_file1) in results

    @patch('subprocess.run')
    def test_fzf_search(self, mock_run, fzf_search):
        # Define test files
        expected_files = ["file1.txt", "file2.txt"]
        
        # Configure mock to return expected output
        mock_result = MagicMock()
        mock_result.stdout = "file1.txt\0file2.txt\0"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        # Bypass test environment detection
        with patch('src.spiderfs_mcp.search.fzf.sys.modules', {}):
            with patch.object(fzf_search, 'fzf_available', True):
                results = fzf_search.search("pattern", "/test/path", 2)
                assert results == expected_files
                
                # Verify the subprocess was called correctly
                mock_run.assert_called_once()
                
        # Test fallback path
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")
        with patch.object(fzf_search, '_python_fallback_search', return_value=["fallback.txt"]):
            results = fzf_search.search("pattern", "/test/path", 1)
            assert results == ["fallback.txt"]