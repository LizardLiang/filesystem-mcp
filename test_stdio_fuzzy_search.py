import json
import sys
import os

def create_test_payloads():
    """Creates test JSON payloads for testing fuzzy search with stdio"""
    # Get the project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Create payload with include_dirs=True
    with_dirs_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "callTool",
        "params": {
            "name": "fuzzy_file_search",
            "arguments": {
                "pattern": "test",  # Modify this pattern as needed
                "root_path": project_root,
                "max_results": 10,
                "include_dirs": True
            }
        }
    }
    
    # Create payload with include_dirs=False
    without_dirs_payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "callTool",
        "params": {
            "name": "fuzzy_file_search",
            "arguments": {
                "pattern": "test",  # Modify this pattern as needed
                "root_path": project_root,
                "max_results": 10,
                "include_dirs": False
            }
        }
    }
    
    # Write payloads to files
    with open("test_with_dirs.json", "w") as f:
        json.dump(with_dirs_payload, f, indent=2)
    
    with open("test_without_dirs.json", "w") as f:
        json.dump(without_dirs_payload, f, indent=2)
    
    # Also print the payloads for direct copy-paste use
    print("===== Payload with include_dirs=True =====")
    print(json.dumps(with_dirs_payload))
    
    print("\n===== Payload with include_dirs=False =====")
    print(json.dumps(without_dirs_payload))
    
    print("\n===== Instructions =====")
    print("Files created: test_with_dirs.json and test_without_dirs.json")
    print("\nTo test with stdio, use one of these commands:")
    print("cat test_with_dirs.json | python -m spiderfs_mcp.server")
    print("cat test_without_dirs.json | python -m spiderfs_mcp.server")
    print("\nOr pipe the JSON directly:")
    print("echo '<COPY JSON HERE>' | python -m spiderfs_mcp.server")

if __name__ == "__main__":
    create_test_payloads()
