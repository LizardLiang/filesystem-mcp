from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator
from pathlib import Path
from typing import List, Optional

from ..search.ripgrep import RipgrepSearch
from ..search.python_search import PythonSearch


router = APIRouter()


class SearchRequest(BaseModel):
    pattern: str = Field(description="Search pattern to use")
    path: str = Field(description="Path to search in")
    max_matches: Optional[int] = Field(1000, ge=1, description="Maximum number of matches to return")
    
    @model_validator(mode='after')
    def validate_fields(self) -> 'SearchRequest':
        if not self.pattern or len(self.pattern.strip()) < 1:
            raise ValueError("Pattern must not be empty")
        if not self.path or len(self.path.strip()) < 1:
            raise ValueError("Path must not be empty")
        return self


class Match(BaseModel):
    path: str
    line_number: int
    line_content: str


class SearchResponse(BaseModel):
    matches: List[Match]
    error: Optional[str] = None


@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    """
    Search endpoint supporting both ripgrep and fallback Python search
    """
    path_obj = Path(request.path)

    # Validate path
    if not path_obj.exists():
        raise HTTPException(status_code=404, detail="Path not found")

    # Try ripgrep first
    ripgrep = RipgrepSearch()
    result = ripgrep.search(request.pattern, request.path, request.max_matches or 1000)

    # Fall back to Python search if ripgrep fails
    if result.error and "ripgrep error" in result.error:
        python_search = PythonSearch()
        result = python_search.search_file(
            request.pattern, request.path, request.max_matches or 1000
        )

    # Convert to API response format
    return SearchResponse(
        matches=[
            Match(path=m.path, line_number=m.line_number, line_content=m.line_content)
            for m in result.matches
        ],
        error=result.error,
    )

