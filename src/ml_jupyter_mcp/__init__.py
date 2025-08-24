"""
ML Jupyter MCP Server - UV-centric Jupyter kernel execution for Claude
"""

__version__ = "2.0.0"
__author__ = "Mayank Ketkar"

from .server import create_server

__all__ = ["create_server"]