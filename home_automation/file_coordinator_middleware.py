"""Middleware for `FileCoordinator`"""
import os
from logging import Logger
from typing import Optional

from home_automation.config import Config


class FileCoordinatorMiddleware:
    """Middleware invoked by FileCoordinator"""

    config: Config
    logger: Optional[Logger]

    def __init__(self, config: Config, logger: Logger = None):
        self.config = config
        self.logger = logger

    async def test(self, path: str) -> bool:
        """Test if the path is to be handles by this middleware."""
        raise NotImplementedError()

    async def act(self, path: str):
        """Act on the file."""
        raise NotImplementedError()


class LaTeXToPDFMiddleware(FileCoordinatorMiddleware):
    """Middleware that converts LaTeX files to PDFs."""

    async def test(self, path: str) -> bool:
        """Test if the path is to be handles by this middleware."""
        return path.endswith(".tex") and not (
            path.startswith(".") or path.startswith("_")
        )

    async def act(self, path: str):
        """Act on the file."""
        os.system(f"pdflatex '{path}'")
