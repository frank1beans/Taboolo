"""API package - HTTP layer for the application.

Note: The main router has been moved to app.api.router for better organization.
For backward compatibility, we re-export it here.
"""
from app.api.router import api_router

__all__ = ["api_router"]
