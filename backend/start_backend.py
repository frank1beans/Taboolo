"""Entry point used to start the FastAPI backend without auto-reload."""
from __future__ import annotations

import argparse
import uvicorn
from app import main as app_main  # noqa: F401  Ensures PyInstaller bundles the app package.


def main() -> None:
    parser = argparse.ArgumentParser(description="Start the Taboo backend API server.")
    parser.add_argument("--host", default="0.0.0.0", help="Bind address for the server.")
    parser.add_argument(
        "--port",
        default=8000,
        type=int,
        help="Listening port (default: 8000).",
    )
    args = parser.parse_args()

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
