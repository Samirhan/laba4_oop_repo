from PySide6.QtCore import Qt
from PySide6.QtGui import QPen, QBrush

from shapes.base import ShapeBase

class CRectangle(ShapeBase):
    def draw(self, p):
        if self._selected:
            p.setBrush(QBrush(self._fill_color.darker(120)))
            p.setPen(QPen(Qt.darkRed, 2))
        else:
            p.setBrush(QBrush(self._fill_color))
            p.setPen(QPen(self._line_color, 2))
        p.drawRect(self._rect)

    def contains(self, pt):
        return self._rect.contains(pt)

    def type_name(self):
        return "rect"
