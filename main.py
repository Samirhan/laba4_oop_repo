import sys

from abc import ABC, abstractmethod

from typing import List
import os
import importlib.util
from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QPainter, QPen, QBrush, QKeySequence, QAction, QActionGroup, QColor, QUndoStack, QUndoCommand
from PySide6.QtWidgets import QApplication, QWidget, QMainWindow, QColorDialog, QToolBar, QMessageBox, QFileDialog


class IShape(ABC):
    @abstractmethod
    def draw(self, p): ...

    @abstractmethod
    def contains(self, pt): ...

    @abstractmethod
    def set_selected(self, v): ...

    @abstractmethod
    def is_selected(self): ...

    @abstractmethod
    def rect(self): ...

    @abstractmethod
    def set_rect(self, rect, bounds=None): ...

    @abstractmethod
    def move(self, dx, dy, bounds): ...

    @abstractmethod
    def change_size(self, d, bounds): ...

    @abstractmethod
    def set_fill_color(self, color): ...

    @abstractmethod
    def set_line_color(self, color): ...

    @abstractmethod
    def type_name(self): ...

    @abstractmethod
    def save(self, stream): ...

    @abstractmethod
    def load(self, stream, factory = None): ...



class ShapeBase(IShape):
    _MIN_SIZE = 10

    def __init__(self, rect, line_color=Qt.black, fill_color=Qt.white):
        self._rect = QRect(rect).normalized()
        self._line_color = QColor(line_color)
        self._fill_color = QColor(fill_color)
        self._selected = False

    def set_selected(self, v):
        self._selected = bool(v)

    def is_selected(self):
        return self._selected

    def set_fill_color(self, color):
        self._fill_color = QColor(color)

    def set_line_color(self, color):
        self._line_color = QColor(color)

    def rect(self):
        return QRect(self._rect)

    def set_rect(self, rect, bounds=None):
        new_rect = QRect(rect).normalized()

        if new_rect.width() < self._MIN_SIZE or new_rect.height() < self._MIN_SIZE:
            return

        if bounds is not None and not bounds.contains(new_rect):
            return

        self._rect = new_rect


    def move(self, dx, dy, bounds = None):
        moved = self._rect.translated(dx, dy)
        self.set_rect(moved, bounds)



    def change_size(self, d, bounds):
        r = self._rect
        grown = QRect(r.left() - d, r.top() - d,r.width() + 2 * d, r.height() + 2 * d,)
        self.set_rect(grown, bounds)

    def type_name(self):
        return "shape_base"

    def save(self, stream):
        r = self._rect
        stream.write(f"{r.left()} {r.top()} {r.width()} {r.height()}\n")

        lc = self._line_color
        fc = self._fill_color
        stream.write(f"{lc.red()} {lc.green()} {lc.blue()} {lc.alpha()}\n")
        stream.write(f"{fc.red()} {fc.green()} {fc.blue()} {fc.alpha()}\n")

    def load(self, stream, factory = None):
        x, y, w, h = map(int, stream.readline().split())
        self._rect = QRect(x, y, w, h).normalized()

        lr, lg, lb, la = map(int, stream.readline().split())
        fr, fg, fb, fa = map(int, stream.readline().split())

        self._line_color = QColor(lr, lg, lb, la)
        self._fill_color = QColor(fr, fg, fb, fa)
        self._selected = False

    def fill_color(self):
        return QColor(self._fill_color)

    def line_color(self):
        return QColor(self._line_color)


class CCircle(ShapeBase):
    def draw(self, p):
        r = self._rect

        if self._selected:
            p.setBrush(QBrush(self._fill_color.darker(120)))
            p.setPen(QPen(Qt.darkBlue, 2))
        else:
            p.setBrush(QBrush(self._fill_color))
            p.setPen(QPen(self._line_color, 2))

        p.setRenderHint(QPainter.Antialiasing, True)
        p.drawEllipse(r)


    def contains(self, pt):
        r = self._rect
        cx = r.center().x()
        cy = r.center().y()
        radius = r.width() / 2.0
        dx = pt.x() - cx
        dy = pt.y() - cy
        return dx * dx + dy * dy <= radius * radius

    def type_name(self):
        return "circle"



    def change_size(self, d, bounds):
        r = self._rect
        side = r.width()
        new_side = side + 2 * d
        if new_side < self._MIN_SIZE:
            return

        cx = r.center().x()
        cy = r.center().y()

        new_rect = QRect(cx - new_side // 2,cy - new_side // 2,new_side,new_side,)
        ShapeBase.set_rect(self, new_rect, bounds)


class CRectangle(ShapeBase):
    def draw(self, p):
        if self._selected:
            p.setBrush(QBrush(self._fill_color.darker(120)))
            p.setPen(QPen(Qt.darkRed, 2))
        else:
            p.setBrush(QBrush(self._fill_color))
            p.setPen(QPen(self._line_color, 2))
        p.drawRect(self._rect)


    def contains(self, pt):
        return self._rect.contains(pt)

    def type_name(self):
        return "rect"



class CEllipse(ShapeBase):
    def draw(self, p):
        if self._selected:
            p.setBrush(QBrush(self._fill_color.darker(120)))
            p.setPen(QPen(Qt.darkGreen, 2))
        else:
            p.setBrush(QBrush(self._fill_color))
            p.setPen(QPen(self._line_color, 2))
        p.setRenderHint(QPainter.Antialiasing, True)
        p.drawEllipse(self._rect)



    def contains(self, pt):
        r = self._rect
        cx = r.center().x()
        cy = r.center().y()
        rx = r.width() / 2.0
        ry = r.height() / 2.0
        if rx == 0 or ry == 0:
            return False
        dx = pt.x() - cx
        dy = pt.y() - cy
        return (dx * dx) / (rx * rx) + (dy * dy) / (ry * ry) <= 1.0

    def type_name(self):
        return "ellipse"



class Group(IShape):
    def __init__(self, children: List[IShape]):
        self._children = list(children)
        self._selected = False


    def set_selected(self, v):
        self._selected = bool(v)

    def is_selected(self):
        return self._selected


    def set_fill_color(self, color):
        for ch in self._children:
            ch.set_fill_color(color)

    def set_line_color(self, color):
        for ch in self._children:
            ch.set_line_color(color)


    def rect(self):
        if not self._children:
            return QRect(0, 0, 0, 0)

        r = self._children[0].rect()
        left = r.left()
        top = r.top()
        right = r.right()
        bottom = r.bottom()

        for ch in self._children[1:]:
            cr = ch.rect()
            left = min(left, cr.left())
            top = min(top, cr.top())
            right = max(right, cr.right())
            bottom = max(bottom, cr.bottom())

        return QRect(QPoint(left, top), QPoint(right, bottom)).normalized()

    def contains(self, pt):
        for ch in reversed(self._children):
            if ch.contains(pt):
                return True
        return False

    def draw(self, p):
        if not self._selected:
            for ch in self._children:
                ch.draw(p)
            return

        prev = [ch.is_selected() for ch in self._children]
        for ch in self._children:
            ch.set_selected(True)

        for ch in self._children:
            ch.draw(p)

        for ch, old in zip(self._children, prev):
            ch.set_selected(old)

    def move(self, dx, dy, bounds = None):
        if not self._children:
            return

        bbox = self.rect()
        moved = bbox.translated(dx, dy)

        # если bounds не передали — просто двигаем без ограничений
        if bounds is not None:
            bbox = self.rect()
            moved = bbox.translated(dx, dy)

            if moved.left() < bounds.left():
                dx += bounds.left() - moved.left()
            if moved.right() > bounds.right():
                dx -= moved.right() - bounds.right()

            if moved.top() < bounds.top():
                dy += bounds.top() - moved.top()
            if moved.bottom() > bounds.bottom():
                dy -= moved.bottom() - bounds.bottom()

        for ch in self._children:
            ch.move(dx, dy, bounds)

    def change_size(self, d, bounds):
        return

    def set_rect(self, rect, bounds=None):
        cur = self.rect()
        dx = rect.left() - cur.left()
        dy = rect.top() - cur.top()
        self.move(dx, dy, bounds)

    def children(self):
        return list(self._children)

    def type_name(self):
        return "group"

    def save(self, stream):
        stream.write(f"{len(self._children)}\n")
        for ch in self._children:
            stream.write(f"{ch.type_name()}\n")
            ch.save(stream)

    def load(self, stream, factory):
        self._selected = False
        self._children = []

        line = stream.readline()
        if not line:
            raise ValueError("Неожиданный конец файла при чтении группы (count).")

        n = int(line.strip())

        for _ in range(n):
            t = stream.readline()
            if not t:
                raise ValueError("Неожиданный конец файла при чтении типа дочернего объекта группы.")
            type_name = t.strip()

            child = factory.create(type_name)
            child.load(stream,factory)
            self._children.append(child)


class ShapeFactory:
    def __init__(self):
        self._creators = {}

    def register(self, type_name, creator):
        self._creators[type_name] = creator

    def create(self, type_name):
        if type_name not in self._creators:
            raise ValueError(f"Неизвестный тип фигуры в файле: {type_name}")
        return self._creators[type_name]()

    def type_names(self):
        return list(self._creators.keys())






class MyStorage:
    def __init__(self, factory):
        self._items: List[IShape] = []
        self._factory = factory

    def add(self, obj):
        if not isinstance(obj, IShape):
            raise TypeError("MyStorage хранит только фигуры")
        self._items.append(obj)


    def remove_selected(self):
        self._items = [o for o in self._items if not o.is_selected()]


    def clear_selection(self):
        for o in self._items:
            o.set_selected(False)


    def for_each_selected(self, func):
        for sh in self._items:
            if sh.is_selected():
                func(sh)


    def items(self):
        return self._items

    def selected_items(self):
        return [o for o in self._items if o.is_selected()]



    def remove(self, obj):
        for i, o in enumerate(self._items):
            if o is obj:
                del self._items[i]
                return True
        return False

    def save_to_file(self, path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"{len(self._items)}\n")
            for obj in self._items:
                f.write(f"{obj.type_name()}\n")
                obj.save(f)

    def load_from_file(self, path):
        with open(path, "r", encoding="utf-8") as f:
            header = f.readline()
            if not header:
                raise ValueError("Пустой файл")

            count = int(header.strip())
            items = []

            for _ in range(count):
                t = f.readline()
                if not t:
                    raise ValueError("Ошибка чтения")
                type_name = t.strip()

                obj = self._factory.create(type_name)
                obj.load(f,self._factory)
                items.append(obj)

        self._items = items
        self.clear_selection()

    def index_of(self, obj):
        for i, o in enumerate(self._items):
            if o is obj:
                return i
        return -1

    def insert(self, index, obj):
        self._items.insert(index, obj)

    def remove_many(self, objs):
        obj_set = set(objs)
        self._items = [o for o in self._items if o not in obj_set]







# команды ундо



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


def _flatten_shapes(items):
    out = []
    for it in items:
        if isinstance(it, Group):
            out.extend(_flatten_shapes(it.children()))
        else:
            out.append(it)
    return out



class SetFillColorCommand(QUndoCommand):
    def __init__(self, storage, canvas, new_color):
        super().__init__()
        self._storage = storage
        self._canvas = canvas
        self._new = QColor(new_color)

        self._items = _flatten_shapes(storage.selected_items())
        self._old = {sh: sh.fill_color() for sh in self._items}

    def redo(self):
        if not self._items:
            return
        for sh in self._items:
            sh.set_fill_color(self._new)
        self._canvas.update()

    def undo(self):
        if not self._items:
            return
        for sh in self._items:
            sh.set_fill_color(self._old[sh])
        self._canvas.update()


class SetLineColorCommand(QUndoCommand):
    def __init__(self, storage, canvas, new_color):
        super().__init__()
        self._storage = storage
        self._canvas = canvas
        self._new = QColor(new_color)

        self._items = _flatten_shapes(storage.selected_items())
        self._old = {sh: sh.line_color() for sh in self._items}

    def redo(self):
        if not self._items:
            return
        for sh in self._items:
            sh.set_line_color(self._new)
        self._canvas.update()

    def undo(self):
        if not self._items:
            return
        for sh in self._items:
            sh.set_line_color(self._old[sh])
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




#КАНВАС



class Canvas(QWidget):
    HANDLE_SIZE = 7

    def __init__(self, storage, main_window):
        super().__init__()
        self._storage = storage
        self._main_window = main_window
        self.setFocusPolicy(Qt.StrongFocus)

        self._mode = "idle" # допустимые - idle, creating, resizing, moving
        self._active_shape = None
        self._active_handle = None
        self._drag_start = QPoint()
        self._original_rect = QRect()

        self._move_start_rects = None

        self._resize_start_rects = None
        self._resize_items = None

    def _square_for_circle(self, fixed_point, pos):
        dx = pos.x() - fixed_point.x()
        dy = pos.y() - fixed_point.y()

        if dx == 0 and dy == 0:
            return QRect(fixed_point,fixed_point,7 ,7)

        ax = abs(dx)
        ay = abs(dy)

        side = min(ax, ay)

        if side < 10:
            side = 10

        sign_x = 1 if dx >= 0 else -1
        sign_y = 1 if dy >= 0 else -1

        x2 = fixed_point.x() +  sign_x * side
        y2 = fixed_point.y() +  sign_y * side

        return QRect(fixed_point, QPoint(x2, y2)).normalized()



    def paintEvent(self, e):
        qp = QPainter(self)
        qp.fillRect(self.rect(), Qt.white)

        for shape in self._storage.items():
            shape.draw(qp)
            if shape.is_selected():
                self._draw_frame(qp, shape)

        if self._mode == "creating" and self._active_shape:
            self._active_shape.draw(qp)
            self._draw_frame(qp, self._active_shape)




    def _draw_frame(self, qp, shape):
        r = shape.rect()
        qp.setPen(QPen(Qt.darkGray, 1, Qt.DashLine))
        qp.setBrush(Qt.NoBrush)
        qp.drawRect(r)
        qp.setBrush(Qt.black)

        if not isinstance(shape, Group):
            for h in self._handles(shape):
                qp.drawRect(h)

    def _handles(self, shape):
        s = self.HANDLE_SIZE
        r = shape.rect()
        pts = [
            QPoint(r.left(), r.top()),
            QPoint(r.right(), r.top()),
            QPoint(r.right(), r.bottom()),
            QPoint(r.left(), r.bottom()),
        ]

        rects = []
        for pt in pts:
            rect = QRect(pt.x() - s // 2, pt.y() - s // 2, s, s)
            rects.append(rect)
        return rects





    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return

        pos = event.position().toPoint()
        ctrl = bool(event.modifiers() & Qt.ControlModifier)
        tool = self._main_window.current_shape_type

        shape, idx = self._hit_handle(pos)

        if shape:
            if not shape.is_selected():
                self._storage.clear_selection()
                shape.set_selected(True)

            self._mode = "resizing"
            self._active_shape = shape
            self._active_handle = idx
            self._drag_start = pos
            self._original_rect = shape.rect()
            self.update()


            items = [sh for sh in self._storage.selected_items() if not isinstance(sh, Group)]
            self._resize_items = items
            self._resize_start_rects = {sh: sh.rect() for sh in items}

            return


        target = self._hit_shape(pos)

        if target is None:
            if tool == "select":
                self._storage.clear_selection()
                self.update()
                return

            self._storage.clear_selection()
            self._start_create(pos)
            return

        if ctrl:
            target.set_selected(not target.is_selected())
        else:
            if not target.is_selected():
                self._storage.clear_selection()
                target.set_selected(True)

        if tool == "select":
            self._mode = "moving"
            self._active_shape = target
            self._drag_start = pos
            self._move_start_rects = {sh: sh.rect()for sh in self._storage.selected_items()}
        self.update()





    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return

        pos = event.position().toPoint()
        bounds = self.rect()

        if self._mode == "creating" and self._active_shape:
            if isinstance(self._active_shape, CCircle):
                rect = self._square_for_circle(self._drag_start, pos)
            else:
                rect = QRect(self._drag_start, pos).normalized()

            self._active_shape.set_rect(rect, bounds)
            self.update()
            return

        if self._mode == "resizing" and self._active_shape:
            if isinstance(self._active_shape, CCircle):
                r = self._original_rect
                corners = [r.topLeft(),r.topRight(), r.bottomRight(),r.bottomLeft()]

                fixed_point = corners[0]

                if self._active_handle == 0:
                    fixed_point = corners[2]
                if self._active_handle == 1:
                    fixed_point = corners[3]
                if self._active_handle == 2:
                    fixed_point = corners[0]
                if self._active_handle == 3:
                    fixed_point = corners[1]

                rect = self._square_for_circle(fixed_point, pos)
            else:
                rect = self._resize_rect(self._original_rect, self._active_handle, pos)

            self._active_shape.set_rect(rect, bounds)
            self.update()
            return

        if self._mode == "moving" and self._active_shape:
            dx = pos.x() - self._drag_start.x()
            dy = pos.y() - self._drag_start.y()

            def _move(shape):
                shape.move(dx, dy, bounds)

            self._storage.for_each_selected(_move)
            self._drag_start = pos
            self.update()
            return

    def mouseReleaseEvent(self, event):
        if self._mode == "creating" and self._active_shape:
            r = self._active_shape.rect()

            if r.width() < ShapeBase._MIN_SIZE or r.height() < ShapeBase._MIN_SIZE:
                self._active_shape = None
                self._mode = "idle"
                self.update()
                return

            cmd = CreateShapeCommand(self._storage, self, self._active_shape)
            self._main_window._undo.push(cmd)

            self._active_shape = None
            self._mode = "idle"
            self.update()
            return

        if self._mode == "moving" and self._move_start_rects:
            end_rects = {
                sh: sh.rect() for sh in self._storage.selected_items() if sh in self._move_start_rects}

            moved = any(end_rects[sh] != self._move_start_rects[sh] for sh in end_rects)

            if moved:
                cmd = MoveSelectedCommand(
                    self._storage,
                    self,
                    list(end_rects.keys()),
                    self._move_start_rects,
                    end_rects
                )
                self._main_window._undo.push(cmd)

            self._move_start_rects = None

        if self._mode == "resizing" and self._resize_start_rects and self._resize_items:
            end_rects = {sh: sh.rect() for sh in self._resize_items}

            cmd = ResizeByHandleCommand(
                self._storage,
                self,
                self._resize_items,
                self._resize_start_rects,
                end_rects
            )

            if not cmd.isObsolete():
                self._main_window._undo.push(cmd)

            self._resize_start_rects = None
            self._resize_items = None

        self._mode = "idle"
        self._active_shape = None
        self._active_handle = None



    def _hit_shape(self, pos):
        for shape in reversed(self._storage.items()):
            if shape.contains(pos):
                return shape
        return None

    def _hit_handle(self, pos):
        for shape in reversed(self._storage.items()):
            if not shape.is_selected():
                continue
            if isinstance(shape, Group):
                continue
            for idx, h in enumerate(self._handles(shape)):
                if h.contains(pos):
                    return shape, idx
        return None, None


    def _start_create(self, pos):
        rect = QRect(pos, pos)
        t = self._main_window.current_shape_type

        s = self._main_window._factory.create(t)
        s.set_rect(rect)

        self._storage.clear_selection()
        s.set_selected(True)


        self._mode = "creating"
        self._active_shape = s
        self._drag_start = pos
        self._original_rect = rect

    def _resize_rect(self, orig, idx, pos):
        x1 = orig.left()
        y1 = orig.top()
        x2 = orig.right()
        y2 = orig.bottom()

        if idx == 0:
            return QRect(pos, QPoint(x2, y2)).normalized()
        if idx == 1:
            return QRect(QPoint(x1, pos.y()), QPoint(pos.x(), y2)).normalized()
        if idx == 2:
            return QRect(QPoint(x1, y1), pos).normalized()
        if idx == 3:
            return QRect(QPoint(pos.x(), y1), QPoint(x2, pos.y())).normalized()



    def keyPressEvent(self, event):
        key = event.key()
        bounds = self.rect()
        move_s = 5
        size_s = 3

        handled = False

        if key == Qt.Key_Left:
            cmd = MoveByKeyCommand(self._storage, self, -move_s, 0)
            self._main_window._undo.push(cmd)
            handled = True

        elif key == Qt.Key_Right:
            cmd = MoveByKeyCommand(self._storage, self, move_s, 0)
            self._main_window._undo.push(cmd)
            handled = True

        elif key == Qt.Key_Up:
            cmd = MoveByKeyCommand(self._storage, self, 0, -move_s)
            self._main_window._undo.push(cmd)
            handled = True

        elif key == Qt.Key_Down:
            cmd = MoveByKeyCommand(self._storage, self, 0, move_s)
            self._main_window._undo.push(cmd)
            handled = True
        elif key in (Qt.Key_Plus, Qt.Key_Equal):
            cmd = ResizeByKeyCommand(self._storage, self, size_s)
            self._main_window._undo.push(cmd)
            handled = True

        elif key == Qt.Key_Minus:
            cmd = ResizeByKeyCommand(self._storage, self, -size_s)
            self._main_window._undo.push(cmd)
            handled = True

        if handled:
            self.update()
        super().keyPressEvent(event)





class PluginAPI:
    def __init__(self):
        self.Qt = Qt
        self.QRect = QRect
        self.QPoint = QPoint
        self.QColor = QColor
        self.QPen = QPen
        self.QBrush = QBrush

        self.IShape = IShape
        self.ShapeBase = ShapeBase


def load_py_plugins(factory, folder="plugins"):
    api = PluginAPI()

    for fn in os.listdir(folder):
        if not fn.endswith(".py"):
            continue

        path = os.path.join(folder, fn)
        mod_name = f"plugin_{os.path.splitext(fn)[0]}"

        spec = importlib.util.spec_from_file_location(mod_name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        if hasattr(mod, "register"):
            mod.register(factory, api)













class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SUPER PAINT 3000--")
        self.resize(900, 600)


        self._factory = ShapeFactory()
        self._factory.register("circle", lambda: CCircle(QRect(0, 0, 10, 10)))
        self._factory.register("rect", lambda: CRectangle(QRect(0, 0, 10, 10)))
        self._factory.register("ellipse", lambda: CEllipse(QRect(0, 0, 10, 10)))
        self._factory.register("group", lambda: Group([]))

        load_py_plugins(self._factory, "plugins")

        self._undo = QUndoStack(self)

        self._storage = MyStorage(self._factory)
        self.current_shape_type = "circle"

        self._canvas = Canvas(self._storage, self)
        self.setCentralWidget(self._canvas)

        self._create_actions()
        self._create_toolbar()





    def _set_type(self, t):
        self.current_shape_type = t

    def _create_actions(self):

        self.act_select = QAction("Выделение", self, checkable=True)
        self.act_select.triggered.connect(lambda: self._set_type("select"))

        self.shape_action_group = QActionGroup(self)
        self.shape_action_group.setExclusive(True)
        self.shape_action_group.addAction(self.act_select)

        # --- динамические инструменты для фигур ---
        self.shape_actions = {}

        # красивое имя на кнопку (если нет — будет как type_name)
        title_map = {
            "circle": "Круг",
            "rect": "Прямоугольник",
            "ellipse": "Эллипс",
            "triangle": "Треугольник",  # можно не писать — но так красивее
        }

        for t in self._factory.type_names():
            if t == "group":
                continue  # group не инструмент рисования
            if t == "shape_base":
                continue

            act = QAction(title_map.get(t, t), self, checkable=True)
            act.triggered.connect(lambda checked=False, tt=t: self._set_type(tt))

            self.shape_action_group.addAction(act)
            self.shape_actions[t] = act

        # что выбрано по умолчанию
        if "circle" in self.shape_actions:
            self.shape_actions["circle"].setChecked(True)
            self.current_shape_type = "circle"
        else:
            self.act_select.setChecked(True)
            self.current_shape_type = "select"





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
        path, f = QFileDialog.getSaveFileName(self,"Сохранить проект","","Проект (*.txt)")
        if not path:
            return
        self._storage.save_to_file(path)


    def _open_project(self):
        path, f = QFileDialog.getOpenFileName(self,"Открыть проект","","Проект (*.txt)")
        if not path:
            return
        self._storage.load_from_file(path)
        self._canvas.update()






def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
