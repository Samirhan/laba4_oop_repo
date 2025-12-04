import sys

from abc import ABC, abstractmethod

from typing import List

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QPainter, QPen, QBrush, QKeySequence, QAction, QActionGroup, QColor
from PySide6.QtWidgets import QApplication, QWidget, QMainWindow, QColorDialog, QToolBar



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


    def move(self, dx, dy, bounds):
        moved = self._rect.translated(dx, dy)
        self.set_rect(moved, bounds)



    def change_size(self, d, bounds):
        r = self._rect
        grown = QRect(r.left() - d, r.top() - d,r.width() + 2 * d, r.height() + 2 * d,)
        self.set_rect(grown, bounds)



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


class MyStorage:
    def __init__(self):
        self._items: List[IShape] = []

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





    def _draw_frame(self, qp, shape):
        r = shape.rect()
        qp.setPen(QPen(Qt.darkGray, 1, Qt.DashLine))
        qp.setBrush(Qt.NoBrush)
        qp.drawRect(r)
        qp.setBrush(Qt.black)

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
            for idx, h in enumerate(self._handles(shape)):
                if h.contains(pos):
                    return shape, idx
        return None, None


    def _start_create(self, pos):
        rect = QRect(pos, pos)
        t = self._main_window.current_shape_type

        if t == "circle":
            s = CCircle(rect)
        elif t == "rect":
            s = CRectangle(rect)
        else:
            s = CEllipse(rect)

        s.set_selected(True)
        self._storage.add(s)

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

        return orig

    def keyPressEvent(self, event):
        key = event.key()
        bounds = self.rect()
        move_s = 5
        size_s = 3

        handled = False

        if key == Qt.Key_Left:
            self._storage.for_each_selected(lambda sh: sh.move(-move_s, 0, bounds))
            handled = True
        elif key == Qt.Key_Right:
            self._storage.for_each_selected(lambda sh: sh.move(move_s, 0, bounds))
            handled = True
        elif key == Qt.Key_Up:
            self._storage.for_each_selected(lambda sh: sh.move(0, -move_s, bounds))
            handled = True
        elif key == Qt.Key_Down:
            self._storage.for_each_selected(lambda sh: sh.move(0, move_s, bounds))
            handled = True

        elif key in (Qt.Key_Plus, Qt.Key_Equal):
            self._storage.for_each_selected(lambda sh: sh.change_size(size_s, bounds))
            handled = True
        elif key == Qt.Key_Minus:
            self._storage.for_each_selected(lambda sh: sh.change_size(-size_s, bounds))
            handled = True

        elif key == Qt.Key_Delete:
            self._storage.remove_selected()
            handled = True

        if handled:
            self.update()
        super().keyPressEvent(event)



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SUPER PAINT 3000--")
        self.resize(900, 600)

        self._storage = MyStorage()
        self.current_shape_type = "circle"

        self._canvas = Canvas(self._storage, self)
        self.setCentralWidget(self._canvas)

        self._create_actions()
        self._create_toolbar()
        self.addAction(self.act_delete)

    def _set_type(self, t):
        self.current_shape_type = t

    def _create_actions(self):

        self.act_select = QAction("Выделение", self, checkable=True)
        self.act_circle = QAction("Круг", self, checkable=True)
        self.act_rect = QAction("Прямоугольник", self, checkable=True)
        self.act_ellipse = QAction("Эллипс", self, checkable=True)


        self.act_circle.setChecked(True)

        group = QActionGroup(self)
        group.setExclusive(True)
        group.addAction(self.act_select)
        group.addAction(self.act_circle)
        group.addAction(self.act_rect)
        group.addAction(self.act_ellipse)

        self.act_select.triggered.connect(lambda: self._set_type("select"))
        self.act_circle.triggered.connect(lambda: self._set_type("circle"))
        self.act_rect.triggered.connect(lambda: self._set_type("rect"))
        self.act_ellipse.triggered.connect(lambda: self._set_type("ellipse"))


        self.act_fill = QAction("Заливка...", self)
        self.act_fill.triggered.connect(self._fill_color)


        self.act_line = QAction("Контур...", self)
        self.act_line.triggered.connect(self._line_color)


        self.act_delete = QAction("Удалить", self)
        self.act_delete.setShortcut(QKeySequence.Delete)
        self.act_delete.triggered.connect(self._delete_selected)

    def _create_toolbar(self):
        toolbar = QToolBar("Инструменты", self)
        self.addToolBar(toolbar)

        toolbar.addAction(self.act_select)
        toolbar.addSeparator()
        toolbar.addAction(self.act_circle)
        toolbar.addAction(self.act_rect)
        toolbar.addAction(self.act_ellipse)
        toolbar.addSeparator()
        toolbar.addAction(self.act_fill)
        toolbar.addAction(self.act_line)


    def _fill_color(self):
        color = QColorDialog.getColor(parent=self, title="Цвет заливки")
        if not color.isValid():
            return
        self._storage.for_each_selected(lambda o: o.set_fill_color(color))
        self._canvas.update()

    def _line_color(self):
        color = QColorDialog.getColor(parent=self, title="Цвет контура")
        if not color.isValid():
            return
        self._storage.for_each_selected(lambda o: o.set_line_color(color))
        self._canvas.update()

    def _delete_selected(self):
        self._storage.remove_selected()
        self._canvas.update()



def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
