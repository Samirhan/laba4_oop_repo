from PySide6.QtGui import QUndoCommand

class MoveSelectedCommand(QUndoCommand):
    def __init__(self, storage, canvas, items, start_positions, end_positions):
        super().__init__()
        self._storage = storage
        self._canvas = canvas
        self._items = items
        self._start = start_positions
        self._end = end_positions

    def redo(self):
        bounds = self._canvas.rect()
        for sh in self._items:
            sh.set_rect(self._end[sh], bounds)
        self._canvas.update()

    def undo(self):
        bounds = self._canvas.rect()
        for sh in self._items:
            sh.set_rect(self._start[sh], bounds)
        self._canvas.update()


class MoveByKeyCommand(QUndoCommand):
    def __init__(self, storage, canvas, dx, dy):
        super().__init__()
        self._storage = storage
        self._canvas = canvas
        self._dx = dx
        self._dy = dy

        self._items = storage.selected_items()
        self._start = {sh: sh.rect() for sh in self._items}
        self._end = None

    def redo(self):
        if not self._items:
            return
        bounds = self._canvas.rect()

        if self._end is None:
            for sh in self._items:
                sh.move(self._dx, self._dy, bounds)
            self._end = {sh: sh.rect() for sh in self._items}
        else:
            for sh in self._items:
                sh.set_rect(self._end[sh], bounds)

        self._canvas.update()

    def undo(self):
        if not self._items:
            return
        bounds = self._canvas.rect()
        for sh in self._items:
            sh.set_rect(self._start[sh], bounds)
        self._canvas.update()
