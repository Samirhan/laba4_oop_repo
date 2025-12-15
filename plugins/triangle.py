from PySide6.QtGui import QPolygon


def register(factory, api):
    Qt = api.Qt
    QRect = api.QRect
    QPoint = api.QPoint
    QColor = api.QColor
    QPen = api.QPen
    QBrush = api.QBrush
    ShapeBase = api.ShapeBase

    class CTriangle(ShapeBase):
        def draw(self, p):
            r = self._rect
            pts = [
                QPoint(r.center().x(), r.top()),
                QPoint(r.left(), r.bottom()),
                QPoint(r.right(), r.bottom()),
            ]

            if self._selected:
                p.setBrush(QBrush(self._fill_color.darker(120)))
                p.setPen(QPen(Qt.darkMagenta, 2))
            else:
                p.setBrush(QBrush(self._fill_color))
                p.setPen(QPen(self._line_color, 2))

            p.drawPolygon(pts)

        def contains(self, pt):
            r = self._rect
            tri = QPolygon([
                QPoint(r.center().x(), r.top()),
                QPoint(r.left(), r.bottom()),
                QPoint(r.right(), r.bottom()),
            ])
            return tri.containsPoint(pt, Qt.OddEvenFill)

        def type_name(self):
            return "triangle"

    factory.register("triangle", lambda: CTriangle(QRect(0, 0, 10, 10)))
