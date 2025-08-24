"""
Environment management with UV-first approach
"""

from .uv_manager import UVManager
from .detector import EnvironmentDetector

__all__ = ["UVManager", "EnvironmentDetector"]