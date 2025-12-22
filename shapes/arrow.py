from PySide6.QtCore import QRect, QPoint, QPointF, Qt
from PySide6.QtGui import QPen, QColor
from core.observer import IObserver, Subject, use_move_token
import math
from core.IShape import IShape


class ArrowShape(IShape):
    def __init__(self, src=None, dst=None):
        self._src = None
        self._dst = None

        self.set_src_dst(src, dst)

        self._selected = False
        self._line_color = Qt.black
        self._fill_color = None       # у стрелки заливки нет
        self._pen_width = 2

    def set_src_dst(self, src, dst):
        # отписка
        if isinstance(self._src, Subject):
            self._src.remove_observer(self)

        self._src = src
        self._dst = dst

        # подписка
        if isinstance(self._src, Subject):
            self._src.add_observer(self)

    def on_subject_changed(self, who, event):
        if not isinstance(event, dict):
            return
        if event.get("type") != "moved":
            return

        dx = event.get("dx", 0)
        dy = event.get("dy", 0)
        token = event.get("token")

        if self._dst is None:
            return

        with use_move_token(token):
            bounds = event.get("bounds", None)
            with use_move_token(token):
                self._dst.move(dx, dy, bounds)

    def src(self):
        return self._src

    def dst(self):
        return self._dst

    def set_endpoints(self, src, dst):
        self.set_src_dst(src, dst)

    def _edge_point(self, rect, toward):
        c = rect.center()
        dx = toward.x() - c.x()
        dy = toward.y() - c.y()

        if dx == 0 and dy == 0:
            return c

        hx = rect.width() / 2.0
        hy = rect.height() / 2.0

        tx = hx / abs(dx) if dx != 0 else float("inf")
        ty = hy / abs(dy) if dy != 0 else float("inf")
        t = min(tx, ty)

        return type(c)(c.x() + dx * t, c.y() + dy * t)

    def draw(self, p):
        if self._src is None or self._dst is None:
            return

        cs = self._src.rect().center()
        cd = self._dst.rect().center()

        a = self._edge_point(self._src.rect(), cd)
        b = self._edge_point(self._dst.rect(), cs)

        color = QColor(Qt.red) if self._selected else self._line_color
        pen = QPen(color, self._pen_width)
        p.setPen(pen)

        p.drawLine(a, b)
        self._draw_head(p, a, b)


    def _draw_head(self, p, a, b):
        import math
        dx = b.x() - a.x()
        dy = b.y() - a.y()
        ang = math.atan2(dy, dx)

        size = 10.0 + (self._pen_width - 2) * 2.0

        left = type(b)(
            b.x() - size * math.cos(ang - 0.5),
            b.y() - size * math.sin(ang - 0.5),
        )
        right = type(b)(
            b.x() - size * math.cos(ang + 0.5),
            b.y() - size * math.sin(ang + 0.5),
        )
        p.drawLine(b, left)
        p.drawLine(b, right)

    def contains(self, pt):
        if self._src is None or self._dst is None:
            return False

        r = self.rect()

        return r.contains(pt)


    def is_selected(self):
        return self._selected

    def set_selected(self, v):
        self._selected = v

    def rect(self):
        if self._src is None or self._dst is None:
            return QRect(0, 0, 0, 0)
        cs = self._src.rect().center()
        cd = self._dst.rect().center()
        a = self._edge_point(self._src.rect(), cd)
        b = self._edge_point(self._dst.rect(), cs)

        x1, y1 = min(a.x(), b.x()), min(a.y(), b.y())
        x2, y2 = max(a.x(), b.x()), max(a.y(), b.y())
        pad = int(5 + self._pen_width)
        return QRect(int(x1) - pad, int(y1) - pad, int(x2 - x1) + 2 * pad, int(y2 - y1) + 2 * pad)


    def set_rect(self, r, bounds=None):
        pass

    def move(self, dx, dy, bounds=None):
        # стрелка "двигается" автоматически через src/dst
        pass

    def change_size(self, d, bounds=None):
        step = 1 if d > 0 else -1
        self._pen_width = max(1, self._pen_width + step)


    def fill_color(self):
        return self._fill_color

    def line_color(self):
        return self._line_color



    def set_colors(self, fill_color, border_color):
        if border_color is not None:
            self._line_color = QColor(border_color)
        if fill_color is not None:
            self._fill_color = QColor(fill_color)


    def colors(self):
        return self._fill_color, self._line_color


    def set_fill_color(self, color):
        if color is not None:
            self._line_color = QColor(color)


    def set_line_color(self, color):

        if color is not None:
            self._line_color = QColor(color)


    def type_name(self):
        return "arrow"


    def save(self, f):
        f.write("-1 -1\n")

    def load(self, f, factory):
        f.readline()

    def set_fill_color(self, color):
        self._fill_color = color

    def set_line_color(self, color):
        self._line_color = color