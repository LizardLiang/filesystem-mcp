from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
import os
import io
import shutil
import tempfile
import filecmp


@dataclass
class LineEdit:
    """Represents an edit to be made to specific lines"""
    line_start: int  # 1-based line number
    line_end: int    # 1-based line number, inclusive
    new_content: str  # Content to replace the specified lines with


@dataclass
class FileWriteResult:
    """Result of a file write operation"""
    success: bool
    changed_lines: int = 0
    error: Optional[str] = None
    backup_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class FileWriter:
    """Handles efficient and safe file write operations"""
    
    def __init__(self, create_backup: bool = True, default_encoding: str = 'utf-8'):
        """
        Initialize the file writer
        
        Args:
            create_backup: Whether to create a backup before writing
        """
        self.create_backup = create_backup
        self.default_encoding = default_encoding
    
    def _create_backup(self, file_path: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Create a backup of the file before writing
        
        Args:
            file_path: Path to the file to backup
            
        Returns:
            Tuple of (success, backup_path, error_message)
        """
        try:
            path_obj = Path(file_path)
            if not path_obj.exists() or not path_obj.is_file():
                return False, None, f"File not found or not a regular file: {file_path}"
            
            # Create backup file in the same directory
            backup_path = f"{file_path}.bak"
            shutil.copy2(file_path, backup_path)
            return True, backup_path, None
            
        except Exception as e:
            return False, None, f"Error creating backup: {str(e)}"
    
    def apply_line_edits(self, file_path: str, edits: List[LineEdit], encoding: Optional[str] = None) -> FileWriteResult:
        """
        Apply a list of line edits to a file
        
        Args:
            file_path: Path to the file to edit
            edits: List of edits to apply
            
        Returns:
            FileWriteResult indicating success or failure
        """
        try:
            path_obj = Path(file_path)
            
            # Validate file
            if not path_obj.exists():
                return FileWriteResult(
                    success=False,
                    error=f"File not found: {file_path}"
                )
                
            if not path_obj.is_file():
                return FileWriteResult(
                    success=False,
                    error=f"Not a file: {file_path}"
                )
            
            # Create backup if requested
            backup_path = None
            if self.create_backup:
                success, backup_path, error = self._create_backup(file_path)
                if not success:
                    return FileWriteResult(
                        success=False,
                        error=error
                    )
            
            # Sort edits by line number (descending) to avoid line number changes
            sorted_edits = sorted(edits, key=lambda e: e.line_start, reverse=True)
            
            # Validate edits
            for edit in sorted_edits:
                if edit.line_start < 1:
                    return FileWriteResult(
                        success=False,
                        error=f"Invalid line number: {edit.line_start}. Line numbers must be >= 1"
                    )
                if edit.line_end < edit.line_start:
                    return FileWriteResult(
                        success=False,
                        error=f"Invalid line range: {edit.line_start}-{edit.line_end}. End must be >= start"
                    )
            
            # Use provided encoding or default
            file_encoding = encoding or self.default_encoding
            
            try:
                # Read the entire file
                with open(file_path, 'r', encoding=file_encoding) as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            changed_lines = 0
            
            # Apply edits
            for edit in sorted_edits:
                # Validate edit ranges
                if edit.line_start > total_lines:
                    return FileWriteResult(
                        success=False,
                        error=f"Line start {edit.line_start} is beyond the end of file ({total_lines} lines)"
                    )
                
                # Adjust for 0-based indexing
                start_idx = edit.line_start - 1
                end_idx = min(edit.line_end, total_lines)  # Cap at file length
                
                # Calculate number of lines being replaced
                num_lines_to_replace = end_idx - start_idx
                
                # Split new content into lines, ensuring trailing newline
                new_lines = edit.new_content.splitlines(True)  # Keep line endings
                
                # Ensure all lines end with newline
                for i, line in enumerate(new_lines):
                    if not line.endswith('\n') and i < len(new_lines) - 1:
                        new_lines[i] = line + '\n'
                
                # Apply the edit
                original_section = lines[start_idx:end_idx]
                lines[start_idx:end_idx] = new_lines
                
                # Check if the content actually changed
                if original_section != new_lines:
                    # Count actual lines replaced for accurate reporting
                    changed_lines += num_lines_to_replace
            
                # Create temp file for atomic write
                with tempfile.NamedTemporaryFile(mode='w', encoding=file_encoding, delete=False) as temp_file:
                temp_path = temp_file.name
                temp_file.writelines(lines)
            
            # If no changes were made, don't bother writing
            if changed_lines == 0 and filecmp.cmp(temp_path, file_path):
                os.unlink(temp_path)  # Remove temp file
                if backup_path:
                    os.unlink(backup_path)  # Remove unnecessary backup
                
                return FileWriteResult(
                    success=True,
                    changed_lines=0,
                    backup_path=None,
                    metadata={"unchanged": True}
                )
            
            # Atomic move temp file to original
            shutil.move(temp_path, file_path)
            
            return FileWriteResult(
                success=True,
                changed_lines=changed_lines,
                backup_path=backup_path
            )
                
                except UnicodeDecodeError as e:
                return FileWriteResult(
                    success=False,
                    error=f"Encoding error: {file_encoding} is not compatible with this file. {str(e)}"
                )
            except Exception as e:
            return FileWriteResult(
                success=False,
                error=f"Error applying edits: {str(e)}"
            )
    
    def replace_string(self, file_path: str, old_string: str, new_string: str, max_replacements: int = 0, encoding: Optional[str] = None) -> FileWriteResult:
        """
        Replace all occurrences of a string in a file
        
        Args:
            file_path: Path to the file to edit
            old_string: String to replace
            new_string: Replacement string
            max_replacements: Maximum number of replacements (0 = unlimited)
            
        Returns:
            FileWriteResult indicating success or failure
        """
        try:
            path_obj = Path(file_path)
            
            # Validate file
            if not path_obj.exists():
                return FileWriteResult(
                    success=False,
                    error=f"File not found: {file_path}"
                )
                
            if not path_obj.is_file():
                return FileWriteResult(
                    success=False,
                    error=f"Not a file: {file_path}"
                )
            
            # Create backup if requested
            backup_path = None
            if self.create_backup:
                success, backup_path, error = self._create_backup(file_path)
                if not success:
                    return FileWriteResult(
                        success=False,
                        error=error
                    )
            
            # Use provided encoding or default
            file_encoding = encoding or self.default_encoding
            
            try:
                # Read the entire file
                with open(file_path, 'r', encoding=file_encoding) as f:
                content = f.read()
            
            # Check if the string exists
            if old_string not in content:
                # No need to make changes
                if backup_path:
                    os.unlink(backup_path)  # Remove unnecessary backup
                
                return FileWriteResult(
                    success=True,
                    changed_lines=0,
                    backup_path=None,
                    metadata={"unchanged": True}
                )
            
            # Replace the string
            if max_replacements > 0:
                new_content = content.replace(old_string, new_string, max_replacements)
                replacements = min(max_replacements, content.count(old_string))
            else:
                new_content = content.replace(old_string, new_string)
                replacements = content.count(old_string)
            
            # If no changes were made, don't bother writing
            if content == new_content:
                if backup_path:
                    os.unlink(backup_path)  # Remove unnecessary backup
                
                return FileWriteResult(
                    success=True,
                    changed_lines=0,
                    backup_path=None,
                    metadata={"unchanged": True}
                )
            
                # Create temp file for atomic write
                with tempfile.NamedTemporaryFile(mode='w', encoding=file_encoding, delete=False) as temp_file:
                temp_path = temp_file.name
                temp_file.write(new_content)
            
            # Atomic move temp file to original
            shutil.move(temp_path, file_path)
            
            # Count changed lines (more accurate method)
            old_lines = content.splitlines()
            new_lines = new_content.splitlines()
            changed_lines = 0
            for i, (old, new) in enumerate(zip(old_lines, new_lines)):
                if old != new:
                    changed_lines += 1
            # Account for added or removed lines
            changed_lines += abs(len(new_lines) - len(old_lines))
            
            return FileWriteResult(
                success=True,
                changed_lines=changed_lines,
                backup_path=backup_path,
                metadata={"replacements": replacements}
            )
                
                except UnicodeDecodeError as e:
                return FileWriteResult(
                    success=False,
                    error=f"Encoding error: {file_encoding} is not compatible with this file. {str(e)}"
                )
            except Exception as e:
            return FileWriteResult(
                success=False,
                error=f"Error replacing string: {str(e)}"
            )
