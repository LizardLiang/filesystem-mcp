import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from unittest.mock import patch
from spiderfs_mcp.server import app
from spiderfs_mcp.file.reader import FileReadResult, LineRange


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


def test_read_line_range_success(mock_path_exists, mock_path_is_file):
    with patch("spiderfs_mcp.file.reader.FileReader.read_line_range") as mock_read:
        # Mock successful file read
        mock_read.return_value = FileReadResult(
            content="line 2\nline 3\n",
            line_range=LineRange(start=2, end=3),
            metadata={"file_size": 100, "total_lines": 5},
        )

        response = client.post(
            "/api/v1/file/read/range",
            json={"path": "test.txt", "start_line": 2, "end_line": 3},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "line 2\nline 3\n"
        assert data["range"]["start"] == 2
        assert data["range"]["end"] == 3
        assert data["metadata"]["file_size"] == 100
        assert data["error"] is None


def test_read_line_range_file_not_found():
    with patch.object(Path, "exists") as mock_exists:
        mock_exists.return_value = False

        response = client.post(
            "/api/v1/file/read/range",
            json={"path": "nonexistent.txt", "start_line": 1, "end_line": 5},
        )

        assert response.status_code == 404


def test_read_line_range_not_a_file(mock_path_exists):
    with patch.object(Path, "is_file") as mock_is_file:
        mock_is_file.return_value = False

        response = client.post(
            "/api/v1/file/read/range",
            json={"path": "directory", "start_line": 1, "end_line": 5},
        )

        assert response.status_code == 400


def test_read_line_range_invalid_request():
    response = client.post(
        "/api/v1/file/read/range",
        json={
            "path": "test.txt",
            "start_line": 5,
            "end_line": 3,  # Invalid: end < start
        },
    )

    assert response.status_code == 422  # Validation error


def test_read_line_range_reader_error(mock_path_exists, mock_path_is_file):
    with patch("spiderfs_mcp.file.reader.FileReader.read_line_range") as mock_read:
        # Mock reader error
        mock_read.return_value = FileReadResult(
            content="", line_range=LineRange(start=1, end=5), error="Test error message"
        )

        response = client.post(
            "/api/v1/file/read/range",
            json={"path": "test.txt", "start_line": 1, "end_line": 5},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Test error message"


def test_read_line_context_success(mock_path_exists, mock_path_is_file):
    with patch(
        "spiderfs_mcp.file.reader.FileReader.read_context_around_line"
    ) as mock_read:
        # Mock successful context read
        mock_read.return_value = FileReadResult(
            content="line 2\nline 3\nline 4\n",
            line_range=LineRange(start=2, end=4),
            metadata={
                "file_size": 100,
                "total_lines": 5,
                "target_line": 3,
                "context_lines": 1,
            },
        )

        response = client.post(
            "/api/v1/file/read/context",
            json={"path": "test.txt", "line_number": 3, "context_lines": 1},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "line 2\nline 3\nline 4\n"
        assert data["range"]["start"] == 2
        assert data["range"]["end"] == 4
        assert data["metadata"]["target_line"] == 3
        assert data["metadata"]["context_lines"] == 1


def test_stream_file_by_lines(mock_path_exists, mock_path_is_file):
    with patch(
        "spiderfs_mcp.file.streamer.FileStreamer.stream_file_by_lines"
    ) as mock_stream:
        # Set up mock chunked data
        mock_stream.return_value = [
            ("line 1\nline 2\n", {"chunk_number": 1, "lines_in_chunk": 2}),
            ("line 3\n", {"chunk_number": 2, "lines_in_chunk": 1}),
        ]

        response = client.get("/api/v1/file/stream/lines/test.txt")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/x-ndjson"

        # Parse the NDJSON response (each line is a JSON object)
        chunks = [eval(line) for line in response.content.decode().strip().split("\n")]
        assert len(chunks) == 2
        assert chunks[0]["chunk"] == "line 1\nline 2\n"
        assert chunks[0]["metadata"]["chunk_number"] == 1


def test_stream_file_by_bytes(mock_path_exists, mock_path_is_file):
    with patch(
        "spiderfs_mcp.file.streamer.FileStreamer.stream_file_by_bytes"
    ) as mock_stream:
        # Set up mock chunked data
        mock_stream.return_value = [
            (b"chunk1", {"chunk_number": 1}),
            (b"chunk2", {"chunk_number": 2}),
        ]

        response = client.get("/api/v1/file/stream/bytes/test.txt")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/octet-stream"
        assert response.content == b"chunk1chunk2"
