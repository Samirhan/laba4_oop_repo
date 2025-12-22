from PySide6.QtCore import QRect, QPoint

from core.IShape import IShape
from core.observer import Subject, get_move_token, use_move_token
import uuid

class Group(Subject, IShape ):
    def __init__(self, children):
        Subject.__init__(self)
        self._children = list(children)
        self._selected = False
        self._last_move_token = None

    def set_selected(self, v):
        self._selected = bool(v)

    def is_selected(self):
        return self._selected

    def set_fill_color(self, color):
        for ch in self._children:
            ch.set_fill_color(color)

    def set_line_color(self, color):
        for ch in self._children:
            ch.set_line_color(color)

    def rect(self):
        if not self._children:
            return QRect(0, 0, 0, 0)

        r = self._children[0].rect()
        left, top, right, bottom = r.left(), r.top(), r.right(), r.bottom()

        for ch in self._children[1:]:
            cr = ch.rect()
            left = min(left, cr.left())
            top = min(top, cr.top())
            right = max(right, cr.right())
            bottom = max(bottom, cr.bottom())

        return QRect(QPoint(left, top), QPoint(right, bottom)).normalized()

    def contains(self, pt):
        for ch in reversed(self._children):
            if ch.contains(pt):
                return True
        return False

    def draw(self, p):
        if not self._selected:
            for ch in self._children:
                ch.draw(p)
            return

        prev = [ch.is_selected() for ch in self._children]
        for ch in self._children:
            ch.set_selected(True)
        for ch in self._children:
            ch.draw(p)
        for ch, old in zip(self._children, prev):
            ch.set_selected(old)

    def move(self, dx, dy, bounds=None):
        token = get_move_token() or uuid.uuid4().hex
        if self._last_move_token == token:
            return
        self._last_move_token = token

        if not self._children:
            return

        before = self.rect()

        bbox = before
        moved = bbox.translated(dx, dy)

        if bounds is not None:
            if moved.left() < bounds.left():
                dx += bounds.left() - moved.left()
            if moved.right() > bounds.right():
                dx -= moved.right() - bounds.right()
            if moved.top() < bounds.top():
                dy += bounds.top() - moved.top()
            if moved.bottom() > bounds.bottom():
                dy -= moved.bottom() - bounds.bottom()

        with use_move_token(token):
            for ch in self._children:
                ch.move(dx, dy, bounds)

        after = self.rect()
        adx = after.left() - before.left()
        ady = after.top() - before.top()
        if adx or ady:
            self.notify_everyone({"type": "moved", "dx": adx, "dy": ady, "token": token, "bounds": bounds})

    def change_size(self, d, bounds=None):
        for ch in self._children:
            ch.change_size(d, bounds)

    def set_rect(self, rect, bounds=None):
        cur = self.rect()
        dx = rect.left() - cur.left()
        dy = rect.top() - cur.top()
        self.move(dx, dy, bounds)

    def children(self):
        return list(self._children)

    def type_name(self):
        return "group"

    def save(self, stream):
        stream.write(f"{len(self._children)}\n")
        for ch in self._children:
            stream.write(f"{ch.type_name()}\n")
            ch.save(stream)

    def load(self, stream, factory):
        self._selected = False
        self._children = []

        line = stream.readline()


        n = int(line.strip())

        for _ in range(n):
            t = stream.readline()
            type_name = t.strip()

            child = factory.create(type_name)
            child.load(stream, factory)
            self._children.append(child)

    def children(self):
        return self._children