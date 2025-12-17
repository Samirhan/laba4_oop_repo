import os
import importlib.util
from core.plugin_api import PluginAPI

def load_py_plugins(factory, folder="plugins"):
    api = PluginAPI()

    if not os.path.isdir(folder):
        return

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
