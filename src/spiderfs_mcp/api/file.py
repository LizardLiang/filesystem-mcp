from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator, model_validator
from pathlib import Path
from typing import List, Optional, Dict, Any
import json

from ..file.reader import FileReader, LineRange, FileReadResult
from ..file.streamer import FileStreamer
from ..file.writer import FileWriter, LineEdit, FileWriteResult


router = APIRouter()


class ReadLineRangeRequest(BaseModel):
    path: str = Field(description="Path to the file to read")
    start_line: int = Field(ge=1, description="Start line number (1-based)")
    end_line: int = Field(ge=1, description="End line number (1-based, inclusive)")
    
    @model_validator(mode='after')
    def validate_fields(self) -> 'ReadLineRangeRequest':
        if not self.path or len(self.path.strip()) < 1:
            raise ValueError("Path must not be empty")
        if self.end_line < self.start_line:
            raise ValueError('end_line must be >= start_line')
        return self


class ReadLineContextRequest(BaseModel):
    path: str = Field(description="Path to the file to read")
    line_number: int = Field(ge=1, description="Target line number to read context for")
    context_lines: int = Field(3, ge=0, description="Number of context lines before and after")
    
    @model_validator(mode='after')
    def validate_fields(self) -> 'ReadLineContextRequest':
        if not self.path or len(self.path.strip()) < 1:
            raise ValueError("Path must not be empty")
        return self


class FileContentResponse(BaseModel):
    content: str
    range: Dict[str, int]
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class StreamChunkResponse(BaseModel):
    chunk: str
    metadata: Dict[str, Any]


@router.post("/read/range", response_model=FileContentResponse)
async def read_line_range(request: ReadLineRangeRequest) -> FileContentResponse:
    """
    Read a specific range of lines from a file
    """
    path_obj = Path(request.path)
    
    # Validate path
    if not path_obj.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if not path_obj.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")
    
    # Read the requested range
    reader = FileReader()
    line_range = LineRange(start=request.start_line, end=request.end_line)
    result = reader.read_line_range(request.path, line_range)
    
    if result.error:
        raise HTTPException(status_code=400, detail=result.error)
    
    return FileContentResponse(
        content=result.content,
        range={"start": result.line_range.start, "end": result.line_range.end},
        metadata=result.metadata
    )


@router.post("/read/context", response_model=FileContentResponse)
async def read_line_context(request: ReadLineContextRequest) -> FileContentResponse:
    """
    Read a specific line with context before and after
    """
    path_obj = Path(request.path)
    
    # Validate path
    if not path_obj.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if not path_obj.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")
    
    # Read the requested line with context
    reader = FileReader()
    result = reader.read_context_around_line(
        request.path, 
        request.line_number, 
        request.context_lines
    )
    
    if result.error:
        raise HTTPException(status_code=400, detail=result.error)
    
    return FileContentResponse(
        content=result.content,
        range={"start": result.line_range.start, "end": result.line_range.end},
        metadata=result.metadata
    )


@router.get("/stream/lines/{file_path:path}")
async def stream_file_by_lines(file_path: str, chunk_size: int = 1000):
    """
    Stream a file's contents in chunks of lines
    """
    path_obj = Path(file_path)
    
    # Validate path
    if not path_obj.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if not path_obj.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")
    
    # Create a streaming response
    streamer = FileStreamer(chunk_size=chunk_size)
    
    async def content_generator():
        for content_chunk, metadata in streamer.stream_file_by_lines(file_path):
            # Create a JSON response for each chunk
            chunk_response = StreamChunkResponse(
                chunk=content_chunk,
                metadata=metadata
            )
            # Convert to JSON and add a newline as a delimiter
            yield json.dumps(chunk_response.model_dump()) + "\n"
    
    return StreamingResponse(
        content_generator(),
        media_type="application/x-ndjson"
    )


@router.get("/stream/bytes/{file_path:path}")
async def stream_file_by_bytes(file_path: str, chunk_size: int = 8192):
    """
    Stream a file's raw bytes in chunks
    """
    path_obj = Path(file_path)
    
    # Validate path
    if not path_obj.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if not path_obj.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")
    
    # Create a streaming response of raw bytes
    streamer = FileStreamer()
    
    async def content_generator():
        for chunk, _ in streamer.stream_file_by_bytes(file_path, chunk_size):
            yield chunk
    
    return StreamingResponse(
        content_generator(),
        media_type="application/octet-stream"
    )


class LineEditRequest(BaseModel):
    line_start: int = Field(ge=1, description="Start line number (1-based)")
    line_end: int = Field(ge=1, description="End line number (1-based, inclusive)")
    new_content: str = Field(description="New content to replace the specified lines with")
    
    @model_validator(mode='after')
    def validate_fields(self) -> 'LineEditRequest':
        if self.line_end < self.line_start:
            raise ValueError('line_end must be >= line_start')
        return self


class ApplyLineEditsRequest(BaseModel):
    path: str = Field(description="Path to the file to edit")
    edits: List[LineEditRequest] = Field(description="List of edits to apply")
    create_backup: bool = Field(True, description="Whether to create a backup before writing")
    
    @model_validator(mode='after')
    def validate_fields(self) -> 'ApplyLineEditsRequest':
        if not self.path or len(self.path.strip()) < 1:
            raise ValueError("Path must not be empty")
        if not self.edits or len(self.edits) < 1:
            raise ValueError('At least one edit must be provided')
        return self


class ReplaceStringRequest(BaseModel):
    path: str = Field(description="Path to the file to edit")
    old_string: str = Field(description="String to replace")
    new_string: str = Field(description="Replacement string")
    max_replacements: int = Field(0, ge=0, description="Maximum number of replacements (0 = unlimited)")
    create_backup: bool = Field(True, description="Whether to create a backup before writing")
    
    @model_validator(mode='after')
    def validate_fields(self) -> 'ReplaceStringRequest':
        if not self.path or len(self.path.strip()) < 1:
            raise ValueError("Path must not be empty")
        if not self.old_string or len(self.old_string) < 1:
            raise ValueError("String to replace must not be empty")
        return self


class WriteResult(BaseModel):
    success: bool
    changed_lines: int = 0
    error: Optional[str] = None
    backup_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@router.post("/write/lines", response_model=WriteResult)
async def apply_line_edits(request: ApplyLineEditsRequest) -> WriteResult:
    """
    Apply line-based edits to a file
    """
    path_obj = Path(request.path)
    
    # Validate path
    if not path_obj.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if not path_obj.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")
    
    # Convert API edits to internal format
    edits = [
        LineEdit(
            line_start=edit.line_start,
            line_end=edit.line_end,
            new_content=edit.new_content
        )
        for edit in request.edits
    ]
    
    # Apply the edits
    writer = FileWriter(create_backup=request.create_backup)
    result = writer.apply_line_edits(request.path, edits)
    
    if not result.success and result.error:
        raise HTTPException(status_code=400, detail=result.error)
    
    return WriteResult(
        success=result.success,
        changed_lines=result.changed_lines,
        error=result.error,
        backup_path=result.backup_path,
        metadata=result.metadata
    )


@router.post("/write/replace", response_model=WriteResult)
async def replace_string(request: ReplaceStringRequest) -> WriteResult:
    """
    Replace all occurrences of a string in a file
    """
    path_obj = Path(request.path)
    
    # Validate path
    if not path_obj.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if not path_obj.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")
    
    # Replace the string
    writer = FileWriter(create_backup=request.create_backup)
    result = writer.replace_string(
        request.path,
        request.old_string,
        request.new_string,
        request.max_replacements
    )
    
    if not result.success and result.error:
        raise HTTPException(status_code=400, detail=result.error)
    
    return WriteResult(
        success=result.success,
        changed_lines=result.changed_lines,
        error=result.error,
        backup_path=result.backup_path,
        metadata=result.metadata
    )
