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

        self._items = [o for o in storage.selected_items() if not _is_arrow(o)]

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



def _is_arrow(o) -> bool:
    return hasattr(o, "type_name") and callable(o.type_name) and o.type_name() == "arrow"


def _is_group(o) -> bool:
    return hasattr(o, "type_name") and callable(o.type_name) and o.type_name() == "group" and hasattr(o, "children")


def _expand(o):
    out = {o}
    if _is_group(o):
        for ch in o.children():
            out.update(_expand(ch))
    return out



def _arrow_endpoints(arrow):
    if hasattr(arrow, "src") and callable(arrow.src) and hasattr(arrow, "dst") and callable(arrow.dst):
        return arrow.src(), arrow.dst()
    if hasattr(arrow, "endpoints") and callable(arrow.endpoints):
        return arrow.endpoints()
    return None, None
