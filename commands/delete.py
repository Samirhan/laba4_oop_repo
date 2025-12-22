from PySide6.QtGui import QUndoCommand
from core.observer import Subject

class DeleteSelectedCommand(QUndoCommand):
    def __init__(self, storage, canvas):
        super().__init__()
        self._storage = storage
        self._canvas = canvas

        self._objs = storage.selected_items()
        self._indices = [(storage.index_of(o), o) for o in self._objs]
        self._indices.sort(key=lambda x: x[0])

    def _is_arrow(self, o):
        return getattr(o, "type_name", lambda: "")() == "arrow"

    def redo(self):
        for o in self._objs:
            if self._is_arrow(o):
                src = getattr(o, "src", lambda: None)()
                if isinstance(src, Subject):
                    src.remove_observer(o)

        self._storage.remove_many(self._objs)
        self._canvas.update()

    def undo(self):
        for idx, obj in reversed(self._indices):
            self._storage.insert(idx, obj)

        for o in self._objs:
            if self._is_arrow(o):
                src = getattr(o, "src", lambda: None)()
                if isinstance(src, Subject):
                    src.add_observer(o)

        present = [o for o in self._objs if o in self._storage.items()]
        self._storage.set_selection(present)

        self._canvas.update()
