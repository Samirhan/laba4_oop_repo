from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem
from PySide6.QtCore import Qt

from shapes.group import Group


class StorageTree(QTreeWidget):
    def __init__(self, storage, parent=None):
        super().__init__(parent)
        self._storage = storage
        self._ignore_tree_events = False

        self.setHeaderHidden(True)
        self.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.setRootIsDecorated(True)

        self.setIndentation(20)

        self._obj_to_item = {}

        self.itemSelectionChanged.connect(self._on_tree_selection_changed)

        self.rebuild()


    def on_subject_changed(self, who, event):
        if event == "structure":
            self.rebuild()
        elif event == "selection":
            self.sync_from_storage_selection()

    def rebuild(self):
        self._ignore_tree_events = True
        try:
            self.clear()
            self._obj_to_item = {}

            for obj in self._storage.items():
                self._process_node(self.invisibleRootItem(), obj)

            self.expandAll()
        finally:
            self._ignore_tree_events = False

        self.sync_from_storage_selection()

    def _process_node(self, parent_item, obj):
        title = obj.type_name()
        item = QTreeWidgetItem([title])
        item.setData(0, Qt.UserRole, obj)

        parent_item.addChild(item)
        self._obj_to_item[obj] = item

        if isinstance(obj, Group):
            for child in obj.children():
                self._process_node(item, child)



    def _on_tree_selection_changed(self):
        if self._ignore_tree_events:
            return

        selected_items = self.selectedItems()
        selected_objs = []
        for it in selected_items:
            o = it.data(0, Qt.UserRole)
            if o is not None:
                selected_objs.append(o)

        self._storage.set_selection(selected_objs)

    def sync_from_storage_selection(self):
        self._ignore_tree_events = True
        self.clearSelection()

        for o in self._storage.selected_items():
            it = self._obj_to_item.get(o)
            if it is not None:
                it.setSelected(True)

        self._ignore_tree_events = False

