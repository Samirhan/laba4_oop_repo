import os, sys
from PySide6.QtWidgets import QMainWindow, QColorDialog, QToolBar, QFileDialog, QSplitter
from PySide6.QtGui import QAction, QActionGroup, QKeySequence, QUndoStack
from PySide6.QtCore import QRect

from core.factory import ShapeFactory
from core.storage import MyStorage
from core.plugins_loader import load_py_plugins

from shapes.circle import CCircle
from shapes.rectangle import CRectangle
from shapes.ellipse import CEllipse
from shapes.group import Group
from shapes.arrow import ArrowShape, BiArrowShape



from ui.canvas import Canvas
from ui.storage_tree import StorageTree


from commands.colors import SetFillColorCommand, SetLineColorCommand
from commands.delete import DeleteSelectedCommand
from commands.grouping import GroupSelectedCommand, UngroupSelectedCommand

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SUPER PAINT 3000--")
        self.resize(1200, 900)


        self._factory = ShapeFactory()
        self._factory.register("circle", lambda: CCircle(QRect(0, 0, 10, 10)))
        self._factory.register("rect", lambda: CRectangle(QRect(0, 0, 10, 10)))
        self._factory.register("ellipse", lambda: CEllipse(QRect(0, 0, 10, 10)))
        self._factory.register("group", lambda: Group([]))
        self._factory.register("arrow", lambda: ArrowShape(None, None))
        self._factory.register("bi_arrow", lambda: BiArrowShape(None, None))

        load_py_plugins(self._factory, "plugins")

        self._undo = QUndoStack(self)

        self._storage = MyStorage(self._factory)
        self.current_shape_type = "circle"

        self._canvas = Canvas(self._storage, self)
        self._storage.add_observer(self._canvas)

        self._tree = StorageTree(self._storage, self)
        self._storage.add_observer(self._tree)

        splitter = QSplitter(self)
        splitter.addWidget(self._tree)
        splitter.addWidget(self._canvas)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        self.setCentralWidget(splitter)

        self._create_actions()
        self._create_toolbar()





    def _set_type(self, t):
        self.current_shape_type = t

    def _create_actions(self):

        self.shape_action_group = QActionGroup(self)
        self.shape_action_group.setExclusive(True)

        self.act_select = QAction("Выделение", self, checkable=True)
        self.act_select.triggered.connect(lambda: self._set_type("select"))
        self.shape_action_group.addAction(self.act_select)

        self.act_arrow = QAction("Стрелка", self, checkable=True)
        self.act_arrow.triggered.connect(lambda: self._set_type("arrow"))
        self.shape_action_group.addAction(self.act_arrow)

        self.act_bi_arrow = QAction("Двунаправленная", self, checkable=True)
        self.act_bi_arrow.triggered.connect(lambda: self._set_type("bi_arrow"))
        self.shape_action_group.addAction(self.act_bi_arrow)

        self.shape_actions = {}


        title_map = {
            "circle": "Круг",
            "rect": "Прямоугольник",
            "ellipse": "Эллипс",
            "triangle": "Треугольник",
            "arrow": "Стрелка",
            "bi_arrow": "Двунаправленная"
        }

        for t in self._factory.type_names():
            if t == "group":
                continue
            if t == "shape_base":
                continue
            if t == "arrow":
                continue
            if t == "bi_arrow":
                continue

            act = QAction(title_map.get(t, t), self, checkable=True)
            act.triggered.connect(lambda checked=False, tt=t: self._set_type(tt))

            self.shape_action_group.addAction(act)
            self.shape_actions[t] = act



        self.shape_actions["circle"].setChecked(True)
        self.current_shape_type = "circle"




        self.act_fill = QAction("Заливка...", self)
        self.act_fill.triggered.connect(self._fill_color)


        self.act_line = QAction("Контур...", self)
        self.act_line.triggered.connect(self._line_color)


        self.act_delete = QAction("Удалить", self)
        self.act_delete.setShortcut(QKeySequence.Delete)
        self.act_delete.triggered.connect(self._delete_selected)

        self.act_group = QAction("Группировать", self)
        self.act_group.triggered.connect(self._group_selected)

        self.act_ungroup = QAction("Разгруппировать", self)
        self.act_ungroup.triggered.connect(self._ungroup_selected)

        self.act_save = QAction("Сохранить...", self)
        self.act_save.setShortcut(QKeySequence.Save)
        self.act_save.triggered.connect(self._save_project)

        self.act_open = QAction("Открыть...", self)
        self.act_open.setShortcut(QKeySequence.Open)
        self.act_open.triggered.connect(self._open_project)

        self.act_undo = self._undo.createUndoAction(self, "Отменить")
        self.act_undo.setShortcut(QKeySequence.Undo)




    def _create_toolbar(self):
        toolbar = QToolBar("Инструменты", self)
        self.addToolBar(toolbar)

        toolbar.addAction(self.act_undo)
        toolbar.addSeparator()

        toolbar.addAction(self.act_select)
        toolbar.addAction(self.act_arrow)
        toolbar.addAction(self.act_bi_arrow)

        for t, act in self.shape_actions.items():
            toolbar.addAction(act)

        toolbar.addSeparator()
        toolbar.addAction(self.act_fill)
        toolbar.addAction(self.act_line)

        toolbar.addSeparator()
        toolbar.addAction(self.act_group)
        toolbar.addAction(self.act_ungroup)

        toolbar.addSeparator()
        toolbar.addAction(self.act_open)
        toolbar.addAction(self.act_save)

        toolbar.addSeparator()
        toolbar.addAction(self.act_delete)
        self.addAction(self.act_delete)

        self.addAction(self.act_undo)




    def _fill_color(self):
        if not self._storage.selected_items():
            return
        color = QColorDialog.getColor(parent=self, title="Цвет заливки")
        if not color.isValid():
            return

        cmd = SetFillColorCommand(self._storage, self._canvas, color)
        if any(cmd._old[sh] != cmd._new for sh in cmd._items):
            self._undo.push(cmd)

    def _line_color(self):
        if not self._storage.selected_items():
            return
        color = QColorDialog.getColor(parent=self, title="Цвет контура")
        if not color.isValid():
            return

        cmd = SetLineColorCommand(self._storage, self._canvas, color)
        if any(cmd._old[sh] != cmd._new for sh in cmd._items):
            self._undo.push(cmd)



    def _delete_selected(self):
        cmd = DeleteSelectedCommand(self._storage, self._canvas)
        self._undo.push(cmd)

    def _group_selected(self):
        cmd = GroupSelectedCommand(self._storage, self._canvas)
        if len(self._storage.selected_items()) >= 2:
            self._undo.push(cmd)

    def _ungroup_selected(self):
        cmd = UngroupSelectedCommand(self._storage, self._canvas)
        if any(isinstance(o, Group) for o in self._storage.selected_items()):
            self._undo.push(cmd)

    def _save_project(self):
        path, f = QFileDialog.getSaveFileName(self,"Сохранить проект","saves","Проект (*.txt)")
        if not path:
            return
        self._storage.save_to_file(path)


    def _open_project(self):
        path, f = QFileDialog.getOpenFileName(self,"Открыть проект","saves","Проект (*.txt)")
        if not path:
            return
        self._storage.load_from_file(path)
        self._canvas.update()