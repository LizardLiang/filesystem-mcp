import io
import codecs
from typing import List, Optional, Union

class FileReader:
    """
    A class to read files with support for multiple encodings
    """
    
    @staticmethod
    def read_file(
        file_path: str, 
        encoding: str = 'utf-8', 
        errors: str = 'strict',
        start_line: Optional[int] = None, 
        end_line: Optional[int] = None
    ) -> List[str]:
        """
        Read a file with specified encoding and optional line range
        
        Args:
            file_path (str): Path to the file to read
            encoding (str, optional): Encoding of the file. Defaults to 'utf-8'
            errors (str, optional): Error handling strategy. Defaults to 'strict'
            start_line (int, optional): Starting line number (1-indexed). Defaults to None
            end_line (int, optional): Ending line number (1-indexed). Defaults to None
        
        Returns:
            List[str]: Lines of the file within the specified range
        
        Raises:
            ValueError: If line range is invalid
            LookupError: If the specified encoding is not supported
            FileNotFoundError: If the file does not exist
        """
        # Validate encoding
        try:
            codecs.lookup(encoding)
        except LookupError:
            raise LookupError(f"Unsupported encoding: {encoding}")
        
        # Open file with specified encoding
        with codecs.open(file_path, 'r', encoding=encoding, errors=errors) as file:
            # Read all lines
            all_lines = file.readlines()
            
            # If no line range specified, return all lines
            if start_line is None and end_line is None:
                return all_lines
            
            # Validate line range
            if start_line is not None and start_line < 1:
                raise ValueError(f"Invalid start line: {start_line}. Must be >= 1")
            
            if end_line is not None and end_line > len(all_lines):
                raise ValueError(f"Invalid end line: {end_line}. Exceeds total lines {len(all_lines)}")
            
            # Adjust for 1-indexing to 0-indexing
            start = (start_line - 1) if start_line is not None else 0
            end = end_line if end_line is not None else len(all_lines)
            
            return all_lines[start:end]
    
    @staticmethod
    def detect_encoding(file_path: str, default_encoding: str = 'utf-8') -> str:
        """
        Attempt to detect the encoding of a file
        
        Args:
            file_path (str): Path to the file
            default_encoding (str, optional): Fallback encoding. Defaults to 'utf-8'
        
        Returns:
            str: Detected or default encoding
        """
        encodings_to_try = [
            'utf-8', 'latin-1', 'utf-16', 'ascii', 
            'iso-8859-1', 'windows-1252'
        ]
        
        for encoding in encodings_to_try:
            try:
                with codecs.open(file_path, 'r', encoding=encoding) as file:
                    file.read()
                return encoding
            except (UnicodeDecodeError, LookupError):
                continue
        
        return default_encoding
