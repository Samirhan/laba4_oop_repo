import uuid

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QPainter, QPen

from core.observer import use_move_token
from shapes.base import ShapeBase
from shapes.circle import CCircle
from shapes.group import Group
from shapes.arrow import ArrowShape

from commands.create import CreateShapeCommand
from commands.move import MoveSelectedCommand, MoveByKeyCommand
from commands.resize import ResizeByKeyCommand, ResizeByHandleCommand
from PySide6.QtGui import QKeySequence
from commands.paste import PasteCommand
from io import StringIO

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

        self._arrow_source = None

    def on_subject_changed(self, who, event):
        if event in ("structure", "selection"):
            self.update()

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
        self.setFocus()
        if event.button() != Qt.LeftButton:
            return

        pos = event.position().toPoint()
        ctrl = bool(event.modifiers() & Qt.ControlModifier)
        tool = self._main_window.current_shape_type

        if tool == "arrow":
            target = self._hit_shape(pos)
            if target is None:
                return

            if self._arrow_source is None:
                self._arrow_source = target

                self._storage.set_selection([target]) if hasattr(self._storage, "set_selection") else (
                    self._storage.clear_selection(), target.set_selected(True))
                self.update()
            else:
                if target is self._arrow_source:
                    self._arrow_source = None
                    return

                from commands.create import CreateShapeCommand
                ar = ArrowShape(self._arrow_source, target)
                self._main_window._undo.push(CreateShapeCommand(self._storage, self, ar))


                self._arrow_source = None
                self.update()

            return

        shape, idx = self._hit_handle(pos)

        if shape:
            if not shape.is_selected():
                self._storage.set_selection([shape])

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
                return

            self._storage.clear_selection()
            self._start_create(pos)
            return

        if ctrl:
            self._storage.toggle_selection(target)
        else:
            if not target.is_selected():
                self._storage.set_selection([target])

        if tool == "select":
            self._mode = "moving"
            self._active_shape = target
            self._drag_start = pos

        items = self._storage.selected_items()
        self._move_start_rects = {sh: sh.rect() for sh in items}

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


            items = list(self._move_start_rects.keys()) if self._move_start_rects else self._storage.selected_items()

            token = uuid.uuid4().hex
            with use_move_token(token):
                for sh, start_rect in self._move_start_rects.items():
                    sh.move(dx, dy, self.rect())

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
            end_rects = {sh: sh.rect() for sh in self._move_start_rects.keys()}


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

        if event.matches(QKeySequence.Copy):
            self._do_copy()
            return
        if event.matches(QKeySequence.Paste):
            self._do_paste()
            return

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


    def _is_arrow(self, o):
        return hasattr(o, "type_name") and callable(o.type_name) and o.type_name() == "arrow"

    def _expand_desc(self, roots):
        out = set()

        def find_chil(x):
            out.add(x)
            if hasattr(x, "children") and callable(x.children):
                for ch in x.children():
                    find_chil(ch)

        for r in roots:
            find_chil(r)
        return out

    def _do_copy(self):
        sel = self._storage.selected_items()
        roots = [o for o in sel if not self._is_arrow(o)]
        if not roots:
            self._main_window._clipboard = None
            return

        inside = self._expand_desc(roots)

        clip_roots = []
        for r in roots:
            s = StringIO()
            r.save(s)
            clip_roots.append({"type": r.type_name(), "data": s.getvalue(), "orig_root": r})


        arrows = []
        for o in sel:
            if self._is_arrow(o):
                src = o.src()
                dst = o.dst()
                if src in inside and dst in inside:
                    arrows.append({"src_obj": src, "dst_obj": dst})

        self._main_window._clipboard = {"roots": clip_roots, "arrows": arrows}

    def _do_paste(self):
        clip = getattr(self._main_window, "_clipboard", None)
        if not clip or not clip["roots"]:
            return

        cmd = PasteCommand(self._storage, self, self._main_window._factory, clip, offset=(20, 20))
        self._main_window._undo.push(cmd)
