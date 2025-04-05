# Changelog

## [Unreleased]

### Added
- Support for different file encodings:
  - Added encoding parameter to FileReader, FileStreamer, and FileWriter
  - Added encoding parameter to all file operation API endpoints
  - Added proper error handling for encoding issues
  - Set UTF-8 as the default encoding

## [0.2.0] - 2025-04-05

### Fixed
- Improved FileWriter line counting logic for more accurate line change tracking
- Migrated all API models to Pydantic V2 syntax
- Updated field validators to modern model_validator format
- Improved model serialization with model_dump()

### Added
- File reading operations:
  - Implemented FileReader for reading specific line ranges
  - Added context reading around line functionality
  - Added API endpoints for partial file reading
  - Added file metadata support (size, line count)

- File streaming capabilities:
  - Implemented FileStreamer for efficient streaming of large files
  - Added line-based streaming functionality
  - Added byte-based streaming functionality
  - Added API endpoints for file streaming

- File writing operations:
  - Implemented FileWriter with safe file modification support
  - Added line-based edit functionality
  - Added string replacement functionality
  - Implemented atomic writes with rollback capability
  - Implemented backup functionality
  - Added API endpoints for file writing operations

- Test coverage:
  - Added comprehensive tests for all file operations
  - Unit tests for file reading, streaming, and writing
  - API endpoint tests with mock services
  - Error handling test cases

### Changed
- Updated project structure with new file operation modules
- Enhanced server.py to include file operation routers
- Updated documentation with new milestone information

## [0.1.0] - 2024-04-05

### Added
- Initial project setup
- Search functionality with ripgrep integration
- Python fallback search implementation
- API endpoints for search operations
- Test coverage for search functionality