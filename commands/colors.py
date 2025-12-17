from PySide6.QtGui import QUndoCommand
from PySide6.QtGui import QColor
from commands.utils import _flatten_shapes

class SetFillColorCommand(QUndoCommand):
    def __init__(self, storage, canvas, new_color):
        super().__init__()
        self._storage = storage
        self._canvas = canvas
        self._new = QColor(new_color)

        self._items = _flatten_shapes(storage.selected_items())
        self._old = {sh: sh.fill_color() for sh in self._items}

    def redo(self):
        if not self._items:
            return
        for sh in self._items:
            sh.set_fill_color(self._new)
        self._canvas.update()

    def undo(self):
        if not self._items:
            return
        for sh in self._items:
            sh.set_fill_color(self._old[sh])
        self._canvas.update()


class SetLineColorCommand(QUndoCommand):
    def __init__(self, storage, canvas, new_color):
        super().__init__()
        self._storage = storage
        self._canvas = canvas
        self._new = QColor(new_color)

        self._items = _flatten_shapes(storage.selected_items())
        self._old = {sh: sh.line_color() for sh in self._items}

    def redo(self):
        if not self._items:
            return
        for sh in self._items:
            sh.set_line_color(self._new)
        self._canvas.update()

    def undo(self):
        if not self._items:
            return
        for sh in self._items:
            sh.set_line_color(self._old[sh])
        self._canvas.update()
