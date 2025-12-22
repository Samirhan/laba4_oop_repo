# core/observer.py
from typing import Protocol
import contextvars
from contextlib import contextmanager

class IObserver(Protocol):
    def on_subject_changed(self, who, event): ...

_CURRENT_MOVE_TOKEN = contextvars.ContextVar("CURRENT_MOVE_TOKEN", default=None)

def get_move_token():
    return _CURRENT_MOVE_TOKEN.get()

@contextmanager
def use_move_token(token):
    prev = _CURRENT_MOVE_TOKEN.get()
    _CURRENT_MOVE_TOKEN.set(token)
    try:
        yield
    finally:
        _CURRENT_MOVE_TOKEN.set(prev)

class Subject:
    def __init__(self):
        self._observers = []

    def add_observer(self, o):
        if o not in self._observers:
            self._observers.append(o)

    def remove_observer(self, o):
        if o in self._observers:
            self._observers.remove(o)

    def notify_everyone(self, event):
        for o in list(self._observers):
            o.on_subject_changed(self, event)
