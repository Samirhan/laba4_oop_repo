from PySide6.QtGui import QUndoCommand

class ResizeByKeyCommand(QUndoCommand):
    def __init__(self, storage, canvas, d):
        super().__init__()
        self._storage = storage
        self._canvas = canvas
        self._d = d

        self._items = storage.selected_items()
        self._start = {sh: sh.rect() for sh in self._items}
        self._end = None

    def redo(self):
        if not self._items:
            return

        bounds = self._canvas.rect()

        if self._end is None:
            for sh in self._items:
                sh.change_size(self._d, bounds)

            self._end = {sh: sh.rect() for sh in self._items}

            if all(self._end[sh] == self._start[sh] for sh in self._items):
                self.setObsolete(True)
                return
        else:
            for sh in self._items:
                sh.set_rect(self._end[sh], bounds)

        self._canvas.update()

    def undo(self):
        if not self._items or self.isObsolete():
            return
        bounds = self._canvas.rect()
        for sh in self._items:
            sh.set_rect(self._start[sh], bounds)
        self._canvas.update()


class ResizeByHandleCommand(QUndoCommand):
    def __init__(self, storage, canvas, items, start_rects, end_rects):
        super().__init__()
        self._storage = storage
        self._canvas = canvas
        self._items = list(items)
        self._start = dict(start_rects)
        self._end = dict(end_rects)

        if all(self._start[sh] == self._end[sh] for sh in self._items):
            self.setObsolete(True)

    def redo(self):
        if not self._items or self.isObsolete():
            return
        bounds = self._canvas.rect()
        for sh in self._items:
            sh.set_rect(self._end[sh], bounds)
        self._canvas.update()

    def undo(self):
        if not self._items or self.isObsolete():
            return
        bounds = self._canvas.rect()
        for sh in self._items:
            sh.set_rect(self._start[sh], bounds)
        self._canvas.update()
