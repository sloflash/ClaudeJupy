"""
Kernel daemon management for persistent Jupyter execution
"""

from .kernel_daemon import KernelDaemon
from .client import DaemonClient

__all__ = ["KernelDaemon", "DaemonClient"]