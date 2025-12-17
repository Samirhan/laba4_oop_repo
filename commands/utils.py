from shapes.group import Group

def _flatten_shapes(items):
    out = []
    for it in items:
        if isinstance(it, Group):
            out.extend(_flatten_shapes(it.children()))
        else:
            out.append(it)
    return out
