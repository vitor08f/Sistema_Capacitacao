"""Convenience ASGI entrypoint: uvicorn main:app --reload."""
from backend.main import app

__all__ = ["app"]
