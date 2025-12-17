from PySide6.QtGui import QUndoCommand
from shapes.group import Group

class GroupSelectedCommand(QUndoCommand):
    def __init__(self, storage, canvas):
        super().__init__()
        self._storage = storage
        self._canvas = canvas

        self._children = storage.selected_items()
        self._indices = [(storage.index_of(o), o) for o in self._children]
        self._indices.sort(key=lambda x: x[0])

        self._group = None
        self._insert_index = (
            self._indices[0][0]
            if self._indices and self._indices[0][0] >= 0
            else len(storage.items())
        )

    def redo(self):
        if len(self._children) < 2:
            return

        for ch in self._children:
            ch.set_selected(False)

        if self._group is None:
            self._group = Group(self._children)

        self._storage.remove_many(self._children)
        self._storage.insert(self._insert_index, self._group)

        self._storage.clear_selection()
        self._group.set_selected(True)

        self._canvas.update()

    def undo(self):
        if not self._group:
            return
        if self._storage.index_of(self._group) < 0:
            return

        self._storage.remove(self._group)

        for idx, obj in self._indices:
            self._storage.insert(idx, obj)

        self._storage.clear_selection()
        for _, obj in self._indices:
            obj.set_selected(True)

        self._canvas.update()


class UngroupSelectedCommand(QUndoCommand):
    def __init__(self, storage, canvas):
        super().__init__()
        self._storage = storage
        self._canvas = canvas

        self._group = None
        for o in storage.selected_items():
            if isinstance(o, Group):
                self._group = o
                break

        self._index = storage.index_of(self._group)
        self._children = self._group.children() if self._group else []

    def redo(self):
        if not self._group or self._index < 0 or not self._children:
            return

        self._storage.remove(self._group)

        for i, ch in enumerate(self._children):
            self._storage.insert(self._index + i, ch)

        self._storage.clear_selection()
        for ch in self._children:
            ch.set_selected(True)

        self._canvas.update()

    def undo(self):
        if not self._group or self._index < 0 or not self._children:
            return
        self._storage.remove_many(self._children)

        self._storage.clear_selection()
        self._group.set_selected(True)
        self._storage.insert(self._index, self._group)

        self._canvas.update()
