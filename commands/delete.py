from PySide6.QtGui import QUndoCommand

class DeleteSelectedCommand(QUndoCommand):
    def __init__(self, storage, canvas):
        super().__init__()
        self._storage = storage
        self._canvas = canvas

        self._objs = storage.selected_items()
        self._indices = [(storage.index_of(o), o) for o in self._objs]
        self._indices.sort(key=lambda x: x[0])

    def redo(self):
        self._storage.remove_many(self._objs)
        self._canvas.update()

    def undo(self):
        for idx, obj in self._indices:
            if idx < 0:
                self._storage.add(obj)
            else:
                self._storage.insert(idx, obj)

        self._storage.clear_selection()
        for _, obj in self._indices:
            obj.set_selected(True)

        self._canvas.update()
