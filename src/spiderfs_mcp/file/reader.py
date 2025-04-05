from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path
import os
import io


@dataclass
class LineRange:
    """Represents a range of lines in a file"""
    start: int  # 1-based line number
    end: int    # 1-based line number, inclusive


@dataclass
class FileReadResult:
    """Result of a file read operation"""
    content: str
    line_range: LineRange
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class FileReader:
    """Handles efficient partial file reading operations"""
    
    def __init__(self, default_encoding: str = 'utf-8'):
        """
        Initialize the file reader
        
        Args:
            default_encoding: Default encoding to use when reading files
        """
        self.default_encoding = default_encoding
    
    def read_line_range(self, file_path: str, line_range: LineRange, encoding: Optional[str] = None) -> FileReadResult:
        """
        Read a specific range of lines from a file
        
        Args:
            file_path: Path to the file to read
            line_range: Range of lines to read (1-based, inclusive)
            
        Returns:
            FileReadResult containing the requested content
        """
        try:
            path_obj = Path(file_path)
            
            if not path_obj.exists():
                return FileReadResult(
                    content="",
                    line_range=line_range,
                    error=f"File not found: {file_path}"
                )
                
            if not path_obj.is_file():
                return FileReadResult(
                    content="",
                    line_range=line_range,
                    error=f"Not a file: {file_path}"
                )
            
            # Validate line range
            if line_range.start < 1:
                return FileReadResult(
                    content="",
                    line_range=line_range,
                    error="Line numbers must be >= 1"
                )
                
            if line_range.end < line_range.start:
                return FileReadResult(
                    content="",
                    line_range=line_range,
                    error="End line must be >= start line"
                )
            
            # Read the specified lines
            content = []
            line_count = 0
            
            # Use provided encoding or default
            file_encoding = encoding or self.default_encoding
            
            try:
                with open(file_path, 'r', encoding=file_encoding) as f:
                # Skip lines before the range
                for _ in range(line_range.start - 1):
                    line = f.readline()
                    if not line:  # EOF
                        break
                    line_count += 1
                
                # Read lines in the range
                for _ in range(line_range.end - line_range.start + 1):
                    line = f.readline()
                    if not line:  # EOF
                        break
                    content.append(line)
                    line_count += 1
                
                return FileReadResult(
                content="".join(content),
                line_range=line_range,
                metadata={
                    "file_size": os.path.getsize(file_path),
                    "total_lines": line_count,
                }
                )
                
            except UnicodeDecodeError as e:
                return FileReadResult(
                    content="",
                    line_range=line_range,
                    error=f"Encoding error: {file_encoding} is not compatible with this file. {str(e)}"
                )
            except Exception as e:
            return FileReadResult(
                content="",
                line_range=line_range,
                error=f"Error reading file: {str(e)}"
            )
    
    def read_context_around_line(self, file_path: str, line_number: int, context_lines: int = 3, encoding: Optional[str] = None) -> FileReadResult:
        """
        Read a line with surrounding context
        
        Args:
            file_path: Path to the file to read
            line_number: Target line number (1-based)
            context_lines: Number of lines to include before and after
            
        Returns:
            FileReadResult containing the requested content with context
        """
        # Calculate the line range including context, ensuring start >= 1
        start_line = max(1, line_number - context_lines)
        end_line = line_number + context_lines
        
        line_range = LineRange(start=start_line, end=end_line)
        result = self.read_line_range(file_path, line_range, encoding=encoding)
        
        # Add metadata about the context
        if result.metadata is None:
            result.metadata = {}
            
        result.metadata.update({
            "target_line": line_number,
            "context_lines": context_lines
        })
        
        return result
