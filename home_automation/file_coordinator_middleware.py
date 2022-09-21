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
        if os.path.isfile(path.replace(".tex", ".pdf")):
            return False
        return path.endswith(".tex") and not (
            path.startswith(".") or path.startswith("_")
        )

    async def act(self, path: str):
        """Act on the file."""
        directory = os.path.dirname(path)
        home = os.path.expanduser("~")
        os.system(f"cd '{home}' && pdflatex -output-directory={directory} {path}")
        if self.logger:
            self.logger.info("Rendered LaTeX file to PDF: %s", path)
        if self.config.middleware.latex_to_pdf:
            if self.config.middleware.latex_to_pdf.delete_aux_file:
                to_delete = path.replace(".tex", ".aux")
                if os.path.isfile(to_delete):
                    if self.logger:
                        self.logger.info(
                            "Deleting corresponding aux file: %s", to_delete
                        )
                    os.remove(to_delete)
            if self.config.middleware.latex_to_pdf.delete_dvi_file:
                to_delete = path.replace(".tex", ".dvi")
                if os.path.isfile(to_delete):
                    if self.logger:
                        self.logger.info("Deleting corresponding dvi file: %s", path)
                    os.remove(path.replace(".tex", ".dvi"))
            if self.config.middleware.latex_to_pdf.delete_log_file:
                to_delete = path.replace(".tex", ".log")
                if os.path.isfile(to_delete):
                    if self.logger:
                        self.logger.info("Deleting corresponding log file: %s", path)
                    os.remove(path.replace(".tex", ".log"))
