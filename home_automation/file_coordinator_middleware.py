"""Middleware for `FileCoordinator`"""
import os
from logging import Logger
from typing import Optional
import shutil

from home_automation.config import Config

BYPRODUCTS_FILE_EXTENSIONS = ["aux", "dvi", "log", "out", "synctex.gz", "toc"]


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
        if self.config.middleware.latex_to_pdf:
            if self.config.middleware.latex_to_pdf.delete_byproducts:
                for byproduct in BYPRODUCTS_FILE_EXTENSIONS:
                    byproduct_path = path.replace(".tex", f".{byproduct}")
                    if os.path.isfile(byproduct_path):
                        os.remove(byproduct_path)
                        if self.logger:
                            self.logger.info("Deleted byproduct: %s", byproduct_path)
                texlive_dir = os.path.join(directory, "texlive2020")
                if os.path.isdir(texlive_dir):
                    shutil.rmtree(texlive_dir)
                    if self.logger:
                        self.logger.info("Deleted byproduct: %s", texlive_dir)
