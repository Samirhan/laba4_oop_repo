from typing import List
from core.IShape import IShape

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
                obj.load(f, self._factory)
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
