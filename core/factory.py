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
