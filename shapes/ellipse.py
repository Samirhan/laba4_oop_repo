from PySide6.QtCore import Qt
from PySide6.QtGui import QPen, QBrush, QPainter

from shapes.base import ShapeBase

class CEllipse(ShapeBase):
    def draw(self, p: QPainter):
        if self._selected:
            p.setBrush(QBrush(self._fill_color.darker(120)))
            p.setPen(QPen(Qt.darkGreen, 2))
        else:
            p.setBrush(QBrush(self._fill_color))
            p.setPen(QPen(self._line_color, 2))
        p.setRenderHint(QPainter.Antialiasing, True)
        p.drawEllipse(self._rect)

    def contains(self, pt):
        r = self._rect
        cx = r.center().x()
        cy = r.center().y()
        rx = r.width() / 2.0
        ry = r.height() / 2.0
        if rx == 0 or ry == 0:
            return False
        dx = pt.x() - cx
        dy = pt.y() - cy
        return (dx * dx) / (rx * rx) + (dy * dy) / (ry * ry) <= 1.0

    def type_name(self):
        return "ellipse"
