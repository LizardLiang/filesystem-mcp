import sys
import os
from spiderfs_mcp.search.fzf import FzfSearch

def test_functionality():
    # Get the project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Initialize the fuzzy search
    fzf = FzfSearch()
    
    # Test pattern - modify this as needed
    pattern = "test"
    
    # Test with both files and directories
    results_both = fzf.search(
        pattern=pattern,
        root_path=project_root,
        max_results=10,
        include_dirs=True
    )
    
    # Test with files only
    results_files_only = fzf.search(
        pattern=pattern,
        root_path=project_root,
        max_results=10,
        include_dirs=False
    )
    
    print("Results with include_dirs=True:")
    for path in results_both:
        print(f"  {path}")
    
    print("\nResults with include_dirs=False:")
    for path in results_files_only:
        print(f"  {path}")
    
    # Compare results
    directories_found = set(results_both) - set(results_files_only)
    print("\nDirectories found:")
    for directory in directories_found:
        print(f"  {directory}")
    
    print(f"\nSummary:")
    print(f"- Results with directories: {len(results_both)}")
    print(f"- Results without directories: {len(results_files_only)}")
    print(f"- Difference (directories): {len(directories_found)}")

if __name__ == "__main__":
    test_functionality()
