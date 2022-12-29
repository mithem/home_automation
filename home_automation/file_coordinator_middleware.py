"""Middleware for `FileCoordinator`"""
import os
import shutil
from abc import ABC, abstractmethod
from logging import Logger
from typing import Optional

from home_automation.config import Config

BYPRODUCTS_FILE_EXTENSIONS = ["aux", "dvi", "log", "out", "synctex.gz", "toc"]


class FileCoordinatorMiddleware(ABC):
    """Middleware invoked by FileCoordinator"""

    config: Config
    logger: Optional[Logger]

    def __init__(self, config: Config, logger: Optional[Logger] = None):
        self.config = config
        self.logger = logger

    @abstractmethod
    async def test(self, path: str) -> bool:
        """Test if the path is to be handles by this middleware."""

    @abstractmethod
    async def act(self, path: str):
        """Act on the file."""


class LaTeXRelatedMiddleware(FileCoordinatorMiddleware, ABC):
    """Middleware for LaTeX related files"""

    def cleanup(self, path: str):
        """Clean up LaTeX byproducts if configured so."""
        if self.config.middleware.latex:
            if self.config.middleware.latex.delete_byproducts:
                for byproduct in BYPRODUCTS_FILE_EXTENSIONS:
                    byproduct_path = path.replace(".tex", f".{byproduct}")
                    if os.path.isfile(byproduct_path):
                        os.remove(byproduct_path)
                        if self.logger:
                            self.logger.info("Deleted byproduct: %s", byproduct_path)
                directory = os.path.dirname(path)
                texlive_dir = os.path.join(directory, "texlive2020")
                if os.path.isdir(texlive_dir):
                    shutil.rmtree(texlive_dir)
                    if self.logger:
                        self.logger.info("Deleted byproduct: %s", texlive_dir)


class LaTeXToPDFMiddleware(LaTeXRelatedMiddleware):
    """Middleware that converts LaTeX files to PDFs."""

    async def test(self, path: str) -> bool:
        """Test if the path is to be handles by this middleware."""
        if os.path.isfile(path.replace(".tex", ".pdf")):
            return False
        return path.endswith(".tex") and not (
            path.startswith(".") or path.startswith("_")
        )

    async def act(self, path: str):
        """Act on the file."""
        directory = os.path.dirname(path)
        home = os.path.expanduser("~")
        command = f"cd '{home}' && pdflatex -output-directory='{directory}' '{path}'"
        os.system(command)
        os.system(command)  # always compile twice (e.g. for a table of contents)
        if self.logger:
            self.logger.info("Rendered LaTeX file to PDF: %s", path)
        self.cleanup(path)


class MarkdownToPDFMiddleware(LaTeXToPDFMiddleware):
    """Middleware that converts Markdown files to PDFs."""

    async def test(self, path: str) -> bool:
        """Test if the path is to be handles by this middleware."""
        if os.path.isfile(path.replace(".md", ".pdf")):
            return False
        return path.endswith(".md") and not (
            path.startswith(".") or path.startswith("_")
        )

    async def act(self, path: str):
        """Act on the file."""
        home = os.path.expanduser("~")
        command = f"cd '{home}' && pandoc -o '{path.replace('.md', '.pdf')}' '{path}'"
        os.system(command)
        if self.logger:
            self.logger.info("Rendered Markdown file to PDF: %s", path)
        self.cleanup(path)
