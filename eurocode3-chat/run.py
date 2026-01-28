#!/usr/bin/env python3
"""
Run script for Eurocode 3 Structural Design Chat Application.
"""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    """Run the application."""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ███████╗ ██████╗ ██████╗     ██████╗██╗  ██╗ █████╗ ████████╗   ║
║   ██╔════╝██╔════╝ ╚════██╗   ██╔════╝██║  ██║██╔══██╗╚══██╔══╝   ║
║   █████╗  ██║       █████╔╝   ██║     ███████║███████║   ██║      ║
║   ██╔══╝  ██║       ╚═══██╗   ██║     ██╔══██║██╔══██║   ██║      ║
║   ███████╗╚██████╗ ██████╔╝   ╚██████╗██║  ██║██║  ██║   ██║      ║
║   ╚══════╝ ╚═════╝ ╚═════╝     ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝      ║
║                                                              ║
║   Eurocode 3 Structural Design Assistant                     ║
║   Steel Structure Design per EN 1993                         ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

    Starting server at http://{host}:{port}
    API Documentation: http://{host}:{port}/docs

    Press CTRL+C to stop the server.
    """)

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )


if __name__ == "__main__":
    main()
