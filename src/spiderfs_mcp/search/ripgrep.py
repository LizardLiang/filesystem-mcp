from dataclasses import dataclass
from typing import List, Optional
import subprocess
from pathlib import Path


@dataclass
class SearchMatch:
    """Represents a single search match"""

    line_number: int
    line_content: str
    path: str


@dataclass
class SearchResult:
    """Container for search results"""

    matches: List[SearchMatch]
    error: Optional[str] = None


class RipgrepSearch:
    def __init__(self, executable_path: str = "rg"):
        """Initialize ripgrep search with optional custom executable path"""
        self.executable = executable_path

    def search(self, pattern: str, path: str, max_matches: int = 1000) -> SearchResult:
        """
        Search for pattern in path using ripgrep

        Args:
            pattern: Regular expression pattern to search for
            path: Path to search in
            max_matches: Maximum number of matches to return

        Returns:
            SearchResult containing matches or error
        """
        try:
            # Build ripgrep command
            cmd = [
                self.executable,
                "--line-number",  # Show line numbers
                "--no-heading",  # Don't group matches by file
                "-m",
                str(max_matches),  # Limit number of matches
                pattern,
                path,
            ]

            # Run ripgrep
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,  # Don't raise on non-zero exit (no matches)
            )

            # Handle error cases
            if (
                process.returncode != 0 and process.returncode != 1
            ):  # 1 means no matches
                return SearchResult(
                    matches=[], error=f"ripgrep error: {process.stderr}"
                )

            # Parse results
            matches = []
            for line in process.stdout.splitlines():
                if not line:
                    continue

                # Parse ripgrep output format: file:line:content
                # For Windows compatibility, handle drive letters (e.g., C:) in paths
                try:
                    # Initialize variables to avoid unbound variable issues
                    path_part = ""
                    line_num = 0
                    content = ""

                    # Split only on the first colon for the path
                    if ":" in line:
                        # Handle Windows paths (e.g., C:\path\file.txt:10:content)
                        if Path(line.split(":", 1)[0] + ":").drive:
                            # Windows path with drive letter
                            path_part = line.split(":", 1)[0] + ":"
                            rest = line.split(":", 1)[1]
                            path_part += rest.split(":", 1)[0]

                            # Now split the rest to get line number and content
                            rest_parts = rest.split(":", 1)

                            if len(rest_parts) < 2:
                                continue

                            content_parts = rest_parts[1].split(":", 1)
                            line_part = (
                                content_parts[0] if len(content_parts) > 1 else ""
                            )
                            content = content_parts[1] if len(content_parts) > 1 else ""
                            line_num = int(line_part) if line_part.isdigit() else 0
                        else:
                            # Unix path (no drive letter)
                            parts = line.split(":", 2)
                            if len(parts) < 2:
                                # Not enough parts, skip this line
                                continue

                            path_part = parts[0]
                            try:
                                line_num = int(parts[1])
                            except ValueError:
                                # Not a valid line number, skip this line
                                continue
                            content = parts[2] if len(parts) > 2 else ""
                    else:
                        # Fall back if no colon (shouldn't happen with ripgrep)
                        continue

                    matches.append(
                        SearchMatch(
                            path=path_part,
                            line_number=line_num,
                            line_content=content,
                        )
                    )
                except Exception as e:
                    # Add debugging info if needed
                    print(f"Error parsing line '{line}': {str(e)}")
                    continue

            return SearchResult(matches=matches)

        except Exception as e:
            return SearchResult(matches=[], error=f"Search failed: {str(e)}")
