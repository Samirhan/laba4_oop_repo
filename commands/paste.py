# commands/paste.py
from PySide6.QtGui import QUndoCommand
from io import StringIO

from shapes.group import Group



def _children(o):
    if hasattr(o, "children") and callable(o.children):
        return o.children()
    return None


def _deserialize_shape(factory, type_name, data):
    obj = factory.create(type_name)
    obj.load(StringIO(data), factory)
    return obj

def _build_mapping(orig_node, new_node, mapping):
    mapping[orig_node] = new_node
    orig = _children(orig_node)
    new = _children(new_node)
    if orig and new:
        for o_ch, n_ch in zip(orig, new):
            _build_mapping(o_ch, n_ch, mapping)

class PasteCommand(QUndoCommand):
    def __init__(self, storage, canvas, factory, clipboard, offset=(40, 40)):
        super().__init__()
        self._storage = storage
        self._canvas = canvas
        self._factory = factory
        self._clipboard = clipboard
        self._offset = offset

        self._created = None  # список созданных объектов (для undo)

    def redo(self):
        if not self._clipboard or not self._clipboard["roots"]:
            return

        bounds = self._canvas.rect()
        dx, dy = self._offset

        new_roots = []
        mapping = {}

        for item in self._clipboard["roots"]:
            new_obj = _deserialize_shape(self._factory, item["type"], item["data"])
            new_obj.move(dx, dy, bounds)
            new_roots.append(new_obj)
            _build_mapping(item["orig_root"], new_obj, mapping)


        new_arrows = []
        for a in self._clipboard["arrows"]:
            src_orig = a["src_obj"]
            dst_orig = a["dst_obj"]
            src_new = mapping.get(src_orig)
            dst_new = mapping.get(dst_orig)
            if src_new is None or dst_new is None:
                continue
            arr = self._factory.create("arrow")
            arr.set_src_dst(src_new, dst_new)
            new_arrows.append(arr)

        for o in new_roots:
            self._storage.add(o)
        for a in new_arrows:
            self._storage.add(a)

        self._storage.clear_selection()
        for o in new_roots:
            o.set_selected(True)
        for a in new_arrows:
            a.set_selected(True)

        self._created = new_roots + new_arrows
        self._canvas.update()

    def undo(self):
        if not self._created:
            return
        self._storage.remove_many(self._created)
        self._canvas.update()
