from PySide6.QtGui import QUndoCommand

class CreateShapeCommand(QUndoCommand):
    def __init__(self, storage, canvas, shape):
        super().__init__()
        self._storage = storage
        self._canvas = canvas
        self._shape = shape

    def redo(self):
        self._storage.add(self._shape)
        self._storage.clear_selection()
        self._shape.set_selected(True)
        self._canvas.update()

    def undo(self):
        self._storage.remove(self._shape)
        self._canvas.update()
