"""Signal classes for GUI components"""
# pylint: disable=no-name-in-module
from PyQt6.QtCore import QObject, pyqtSignal

class ProgressSignal(QObject):
    """Signal class for thread-safe progress updates"""
    updated = pyqtSignal(int)
    # pylint: disable=too-few-public-methods