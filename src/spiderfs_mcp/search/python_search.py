import re
from pathlib import Path
from typing import List, Generator
from .ripgrep import SearchMatch, SearchResult


class PythonSearch:
    """Fallback Python-based search implementation"""
    
    def search_file(self, pattern: str, path: str, max_matches: int = 1000) -> SearchResult:
        """
        Search a single file for pattern
        
        Args:
            pattern: Regular expression pattern to search for
            path: Path to file to search
            max_matches: Maximum number of matches to return
            
        Returns:
            SearchResult containing matches or error
        """
        try:
            matches: List[SearchMatch] = []
            compiled_pattern = re.compile(pattern)
            
            with open(path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f, 1):
                    if compiled_pattern.search(line):
                        matches.append(SearchMatch(
                            path=path,
                            line_number=i,
                            line_content=line.rstrip('\n')
                        ))
                        
                        if len(matches) >= max_matches:
                            break
                            
            return SearchResult(matches=matches)
            
        except Exception as e:
            return SearchResult(
                matches=[],
                error=f"Search failed: {str(e)}"
            )