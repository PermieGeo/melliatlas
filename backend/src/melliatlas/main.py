"""ASGI application entry point."""

from melliatlas.api.app import create_app

app = create_app()
