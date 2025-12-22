from core.IShape import IShape
from core.observer import Subject

class MyStorage(Subject):
    def __init__(self, factory):
        super().__init__()
        self._items = []

        self._factory = factory

    def add(self, obj):
        if not isinstance(obj, IShape):
            raise TypeError("MyStorage хранит только фигуры")
        self._items.append(obj)
        self.notify_everyone("structure")



    def clear_selection(self):
        changed = False
        for shape in self._items:
            if shape.is_selected():
                shape.set_selected(False)
                changed = True
        if changed:
            self.notify_everyone("selection")

    def set_selection(self, selected):
        selected_set = set(selected)
        changed = False
        for shape in self._items:
            if shape in selected_set:
                should = True
            else:
                should = False
            if shape.is_selected() != should:
                shape.set_selected(should)
                changed = True
        if changed:
            self.notify_everyone("selection")

    def toggle_selection(self, shape):
        if shape not in self._items:
            return
        shape.set_selected(not shape.is_selected())
        self.notify_everyone("selection")

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
                was_selected = o.is_selected()
                self._items.remove(o)
                self.notify_everyone("structure")
                if was_selected:
                    self.notify_everyone("selection")
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
                obj.load(f, self._factory)
                items.append(obj)

        self._items = items
        self.clear_selection()
        self.notify_everyone("structure")
        self.notify_everyone("selection")

    def index_of(self, obj):
        for i, o in enumerate(self._items):
            if o is obj:
                return i
        return -1

    def insert(self, index, obj):
        self._items.insert(index, obj)
        self.notify_everyone("structure")

    def remove_many(self, objs):
        obj_set = set(objs)
        self._items = [o for o in self._items if o not in obj_set]
        self.notify_everyone("structure")
        self.notify_everyone("selection")


