"""SpiderFS MCP module."""

__version__ = "0.1.0"


import click
from pathlib import Path
import logging
import sys
from .server import serve


@click.command()
def main() -> None:
    """MCP File Server - File system operations for MCP"""
    import asyncio

    logging.basicConfig(
        level="INFO",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )

    # Run the server
    asyncio.run(serve())


if __name__ == "__main__":
    main()

