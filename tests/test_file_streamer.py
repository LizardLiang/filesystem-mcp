import pytest
from unittest.mock import patch, mock_open
from pathlib import Path
from spiderfs_mcp.file.streamer import FileStreamer


def test_stream_file_by_lines():
    mock_file_content = "line 1\nline 2\nline 3\nline 4\nline 5\n"
    
    with patch("builtins.open", mock_open(read_data=mock_file_content)):
        with patch.object(Path, "exists") as mock_exists:
            with patch.object(Path, "is_file") as mock_is_file:
                with patch("os.path.getsize") as mock_getsize:
                    mock_exists.return_value = True
                    mock_is_file.return_value = True
                    mock_getsize.return_value = len(mock_file_content)
                    
                    streamer = FileStreamer(chunk_size=2)  # 2 lines per chunk
                    chunks = list(streamer.stream_file_by_lines("test.txt"))
                    
                    # Should have 3 chunks: 2 lines, 2 lines, 1 line
                    assert len(chunks) == 3
                    
                    # First chunk should have lines 1-2
                    content, metadata = chunks[0]
                    assert content == "line 1\nline 2\n"
                    assert metadata["chunk_number"] == 1
                    assert metadata["lines_in_chunk"] == 2
                    
                    # Second chunk should have lines 3-4
                    content, metadata = chunks[1]
                    assert content == "line 3\nline 4\n"
                    assert metadata["chunk_number"] == 2
                    assert metadata["lines_in_chunk"] == 2
                    
                    # Third chunk should have line 5
                    content, metadata = chunks[2]
                    assert content == "line 5\n"
                    assert metadata["chunk_number"] == 3
                    assert metadata["lines_in_chunk"] == 1


def test_stream_file_by_lines_file_not_found():
    with patch.object(Path, "exists") as mock_exists:
        mock_exists.return_value = False
        
        streamer = FileStreamer()
        chunks = list(streamer.stream_file_by_lines("nonexistent.txt"))
        
        # Should have one error chunk
        assert len(chunks) == 1
        content, metadata = chunks[0]
        assert content == ""
        assert "error" in metadata
        assert "File not found" in metadata["error"]


def test_stream_file_by_lines_not_a_file():
    with patch.object(Path, "exists") as mock_exists:
        with patch.object(Path, "is_file") as mock_is_file:
            mock_exists.return_value = True
            mock_is_file.return_value = False
            
            streamer = FileStreamer()
            chunks = list(streamer.stream_file_by_lines("directory"))
            
            # Should have one error chunk
            assert len(chunks) == 1
            content, metadata = chunks[0]
            assert content == ""
            assert "error" in metadata
            assert "not a regular file" in metadata["error"]


def test_stream_file_by_lines_read_error():
    with patch.object(Path, "exists") as mock_exists:
        with patch.object(Path, "is_file") as mock_is_file:
            with patch("builtins.open") as mock_open_func:
                mock_exists.return_value = True
                mock_is_file.return_value = True
                mock_open_func.side_effect = Exception("Mock I/O error")
                
                streamer = FileStreamer()
                chunks = list(streamer.stream_file_by_lines("test.txt"))
                
                # Should have one error chunk
                assert len(chunks) == 1
                content, metadata = chunks[0]
                assert content == ""
                assert "error" in metadata
                assert "Error streaming file" in metadata["error"]


def test_stream_file_by_bytes():
    mock_file_content = b"0123456789" * 10  # 100 bytes
    
    with patch("builtins.open", mock_open(read_data=mock_file_content)):
        with patch.object(Path, "exists") as mock_exists:
            with patch.object(Path, "is_file") as mock_is_file:
                with patch("os.path.getsize") as mock_getsize:
                    mock_exists.return_value = True
                    mock_is_file.return_value = True
                    mock_getsize.return_value = len(mock_file_content)
                    
                    streamer = FileStreamer()
                    chunks = list(streamer.stream_file_by_bytes("test.txt", byte_chunk_size=30))
                    
                    # Should have 4 chunks of 30 bytes, except the last one with only 10 bytes
                    assert len(chunks) == 4
                    
                    # First chunk should be 30 bytes
                    chunk, metadata = chunks[0]
                    assert len(chunk) == 30
                    assert metadata["chunk_number"] == 1
                    assert metadata["bytes_in_chunk"] == 30
                    assert metadata["is_last_chunk"] is False
                    
                    # Last chunk should be 10 bytes
                    chunk, metadata = chunks[3]
                    assert len(chunk) == 10
                    assert metadata["chunk_number"] == 4
                    assert metadata["bytes_in_chunk"] == 10
                    assert metadata["is_last_chunk"] is True


def test_stream_file_by_bytes_file_not_found():
    with patch.object(Path, "exists") as mock_exists:
        mock_exists.return_value = False
        
        streamer = FileStreamer()
        chunks = list(streamer.stream_file_by_bytes("nonexistent.txt"))
        
        # Should have one error chunk
        assert len(chunks) == 1
        chunk, metadata = chunks[0]
        assert chunk == b""
        assert "error" in metadata
        assert "File not found" in metadata["error"]


def test_stream_file_by_bytes_read_error():
    with patch.object(Path, "exists") as mock_exists:
        with patch.object(Path, "is_file") as mock_is_file:
            with patch("builtins.open") as mock_open_func:
                mock_exists.return_value = True
                mock_is_file.return_value = True
                mock_open_func.side_effect = Exception("Mock I/O error")
                
                streamer = FileStreamer()
                chunks = list(streamer.stream_file_by_bytes("test.txt"))
                
                # Should have one error chunk
                assert len(chunks) == 1
                chunk, metadata = chunks[0]
                assert chunk == b""
                assert "error" in metadata
                assert "Error streaming file" in metadata["error"]