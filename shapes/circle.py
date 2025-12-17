from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QPainter, QPen, QBrush

from shapes.base import ShapeBase

class CCircle(ShapeBase):
    def draw(self, p: QPainter):
        r = self._rect

        if self._selected:
            p.setBrush(QBrush(self._fill_color.darker(120)))
            p.setPen(QPen(Qt.darkBlue, 2))
        else:
            p.setBrush(QBrush(self._fill_color))
            p.setPen(QPen(self._line_color, 2))

        p.setRenderHint(QPainter.Antialiasing, True)
        p.drawEllipse(r)

    def contains(self, pt):
        r = self._rect
        cx = r.center().x()
        cy = r.center().y()
        radius = r.width() / 2.0
        dx = pt.x() - cx
        dy = pt.y() - cy
        return dx * dx + dy * dy <= radius * radius

    def type_name(self):
        return "circle"

    def change_size(self, d, bounds=None):
        r = self._rect
        side = r.width()
        new_side = side + 2 * d
        if new_side < self._MIN_SIZE:
            return

        cx = r.left() + r.width() / 2.0
        cy = r.top() + r.height() / 2.0

        half = new_side / 2.0
        left = int(round(cx - half))
        top = int(round(cy - half))

        new_rect = QRect(left, top, int(new_side), int(new_side))
        ShapeBase.set_rect(self, new_rect, bounds)
