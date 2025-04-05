import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from unittest.mock import patch
from spiderfs_mcp.server import app
from spiderfs_mcp.search.ripgrep import SearchResult, SearchMatch


client = TestClient(app)


@pytest.fixture
def mock_path_exists():
    with patch.object(Path, "exists") as mock_exists:
        mock_exists.return_value = True
        yield mock_exists


def test_search_ripgrep_success(mock_path_exists):
    with patch("spiderfs_mcp.search.ripgrep.RipgrepSearch.search") as mock_search:
        # Mock successful ripgrep search
        mock_search.return_value = SearchResult(
            matches=[
                SearchMatch(
                    path="test.txt",
                    line_number=1,
                    line_content="hello world"
                )
            ]
        )
        
        response = client.post(
            "/api/v1/search",
            json={
                "pattern": "hello",
                "path": "test.txt",
                "max_matches": 10
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["matches"]) == 1
        assert data["matches"][0]["line_content"] == "hello world"
        assert data["error"] is None


def test_search_fallback_to_python(mock_path_exists):
    with patch("spiderfs_mcp.search.ripgrep.RipgrepSearch.search") as mock_rg_search:
        with patch("spiderfs_mcp.search.python_search.PythonSearch.search_file") as mock_py_search:
            # Mock ripgrep failure
            mock_rg_search.return_value = SearchResult(
                matches=[],
                error="ripgrep error: command not found"
            )
            
            # Mock successful Python search
            mock_py_search.return_value = SearchResult(
                matches=[
                    SearchMatch(
                        path="test.txt",
                        line_number=1,
                        line_content="hello world"
                    )
                ]
            )
            
            response = client.post(
                "/api/v1/search",
                json={
                    "pattern": "hello",
                    "path": "test.txt"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["matches"]) == 1
            assert mock_py_search.called


def test_search_path_not_found():
    with patch.object(Path, "exists") as mock_exists:
        mock_exists.return_value = False
        
        response = client.post(
            "/api/v1/search",
            json={
                "pattern": "hello",
                "path": "nonexistent.txt"
            }
        )
        
        assert response.status_code == 404


def test_search_invalid_request():
    response = client.post(
        "/api/v1/search",
        json={
            "pattern": "",  # Empty pattern
            "path": "test.txt"
        }
    )
    
    assert response.status_code == 422  # Validation error