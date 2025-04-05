from typing import Iterator, Optional, Dict, Any, Tuple
from pathlib import Path
import os


class FileStreamer:
    """Handles streaming file contents in manageable chunks"""
    
    def __init__(self, chunk_size: int = 1000, default_encoding: str = 'utf-8'):
        """
        Initialize the file streamer
        
        Args:
            chunk_size: Number of lines per chunk
        """
        self.chunk_size = chunk_size
        self.default_encoding = default_encoding
        
    def stream_file_by_lines(self, file_path: str, encoding: Optional[str] = None) -> Iterator[Tuple[str, Dict[str, Any]]]:
        """
        Stream a file's contents in chunks of lines
        
        Args:
            file_path: Path to the file to stream
            
        Yields:
            Tuple of (content_chunk, metadata)
        """
        try:
            path_obj = Path(file_path)
            
            if not path_obj.exists() or not path_obj.is_file():
                yield "", {
                    "error": f"File not found or not a regular file: {file_path}",
                    "chunk_number": 0,
                    "total_chunks": 0
                }
                return
                
            file_size = os.path.getsize(file_path)
            total_lines = 0
            chunk_number = 0
            
            # Use provided encoding or default
            file_encoding = encoding or self.default_encoding
            
            try:
                with open(file_path, 'r', encoding=file_encoding) as f:
                while True:
                    # Read a chunk of lines
                    lines = []
                    for _ in range(self.chunk_size):
                        line = f.readline()
                        if not line:  # EOF
                            break
                        lines.append(line)
                        total_lines += 1
                    
                    # If we read something, yield it
                    if lines:
                        chunk_number += 1
                        content_chunk = "".join(lines)
                        
                        # Create metadata for this chunk
                        metadata = {
                            "chunk_number": chunk_number,
                            "lines_in_chunk": len(lines),
                            "file_size": file_size,
                            "lines_read_so_far": total_lines,
                        }
                        
                        yield content_chunk, metadata
                    else:
                        # No more lines to read
                        break
            
            except UnicodeDecodeError as e:
                yield "", {
                    "error": f"Encoding error: {file_encoding} is not compatible with this file. {str(e)}",
                    "chunk_number": 0,
                    "total_chunks": 0
                }
                        
        except Exception as e:
            yield "", {
                "error": f"Error streaming file: {str(e)}",
                "chunk_number": 0,
                "total_chunks": 0
            }
            
    def stream_file_by_bytes(self, file_path: str, byte_chunk_size: int = 8192, binary_mode: bool = True) -> Iterator[Tuple[bytes, Dict[str, Any]]]:
        """
        Stream a file's contents in chunks of bytes
        
        Args:
            file_path: Path to the file to stream
            byte_chunk_size: Size of each chunk in bytes
            binary_mode: Whether to open the file in binary mode
            
        Yields:
            Tuple of (bytes_chunk, metadata)
        """
        """
        Stream a file's contents in chunks of bytes
        
        Args:
            file_path: Path to the file to stream
            byte_chunk_size: Size of each chunk in bytes
            
        Yields:
            Tuple of (bytes_chunk, metadata)
        """
        try:
            path_obj = Path(file_path)
            
            if not path_obj.exists() or not path_obj.is_file():
                yield b"", {
                    "error": f"File not found or not a regular file: {file_path}",
                    "chunk_number": 0,
                    "total_chunks": 0
                }
                return
                
            file_size = os.path.getsize(file_path)
            estimated_chunks = (file_size + byte_chunk_size - 1) // byte_chunk_size
            bytes_read = 0
            chunk_number = 0
            
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(byte_chunk_size)
                    if not chunk:  # EOF
                        break
                    
                    chunk_number += 1
                    bytes_read += len(chunk)
                    
                    # Create metadata for this chunk
                    metadata = {
                        "chunk_number": chunk_number,
                        "estimated_total_chunks": estimated_chunks,
                        "bytes_in_chunk": len(chunk),
                        "file_size": file_size,
                        "bytes_read_so_far": bytes_read,
                        "is_last_chunk": bytes_read >= file_size
                    }
                    
                    yield chunk, metadata
                        
        except Exception as e:
            yield b"", {
                "error": f"Error streaming file: {str(e)}",
                "chunk_number": 0,
                "total_chunks": 0
            }
