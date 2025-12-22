from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor

from core.IShape import IShape
import uuid
from core.observer import Subject, get_move_token

class ShapeBase(Subject, IShape):
    _MIN_SIZE = 10

    def __init__(self, rect, line_color=Qt.black, fill_color=Qt.white):
        Subject.__init__(self)
        self._rect = QRect(rect).normalized()
        self._line_color = QColor(line_color)
        self._fill_color = QColor(fill_color)
        self._selected = False
        self._last_move_token = None

    def set_selected(self, v):
        self._selected = bool(v)

    def is_selected(self):
        return self._selected

    def set_fill_color(self, color):
        self._fill_color = QColor(color)

    def set_line_color(self, color):
        self._line_color = QColor(color)

    def rect(self):
        return QRect(self._rect)

    def set_rect(self, rect, bounds=None):
        new_rect = QRect(rect).normalized()

        if new_rect.width() < self._MIN_SIZE or new_rect.height() < self._MIN_SIZE:
            return

        if bounds is not None and not bounds.contains(new_rect):
            return

        self._rect = new_rect

    def move(self, dx, dy, bounds=None):
        token = get_move_token() or uuid.uuid4().hex
        if self._last_move_token == token:
            return
        self._last_move_token = token

        before = QRect(self._rect)
        moved = self._rect.translated(dx, dy)
        self.set_rect(moved, bounds)
        after = QRect(self._rect)

        adx = after.left() - before.left()
        ady = after.top() - before.top()
        if adx or ady:
            self.notify_everyone({"type": "moved", "dx": adx, "dy": ady, "token": token, "bounds": bounds})

    def change_size(self, d, bounds):
        r = self._rect
        grown = QRect(r.left() - d, r.top() - d, r.width() + 2 * d, r.height() + 2 * d)
        self.set_rect(grown, bounds)

    def type_name(self):
        return "shape_base"

    def save(self, stream):
        r = self._rect
        stream.write(f"{r.left()} {r.top()} {r.width()} {r.height()}\n")

        lc = self._line_color
        fc = self._fill_color
        stream.write(f"{lc.red()} {lc.green()} {lc.blue()} {lc.alpha()}\n")
        stream.write(f"{fc.red()} {fc.green()} {fc.blue()} {fc.alpha()}\n")

    def load(self, stream, factory=None):
        x, y, w, h = map(int, stream.readline().split())
        self._rect = QRect(x, y, w, h).normalized()

        lr, lg, lb, la = map(int, stream.readline().split())
        fr, fg, fb, fa = map(int, stream.readline().split())

        self._line_color = QColor(lr, lg, lb, la)
        self._fill_color = QColor(fr, fg, fb, fa)
        self._selected = False

    def fill_color(self):
        return QColor(self._fill_color)

    def line_color(self):
        return QColor(self._line_color)
