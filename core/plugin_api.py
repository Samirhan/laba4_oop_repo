from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QColor, QPen, QBrush

from core.IShape import IShape
from shapes.base import ShapeBase

class PluginAPI:
    def __init__(self):
        self.Qt = Qt
        self.QRect = QRect
        self.QPoint = QPoint
        self.QColor = QColor
        self.QPen = QPen
        self.QBrush = QBrush

        self.IShape = IShape
        self.ShapeBase = ShapeBase
