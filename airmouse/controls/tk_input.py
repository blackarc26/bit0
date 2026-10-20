import tkinter as tk
from typing import Dict, Mapping

from .commands import Command
from .keyboard_input import KeyboardInput


class TkKeyboardInput(KeyboardInput):
    """Key capture through Tk. Works only while one of the app's windows
    (control panel or whiteboard) has focus, but is safe on every OS.

    macOS Tk reports a held key as a stream of release+press pairs. A
    release is therefore delayed by `release_grace_ms`, and cancelled if
    the same key is pressed again within that time.
    """

    def __init__(
        self,
        root: tk.Tk,
        bindings: Mapping[str, Command],
        release_grace_ms: int = 120,
    ):
        super().__init__(bindings)
        self._root = root
        self._grace_ms = release_grace_ms
        self._pending_release: Dict[str, str] = {}

    def start(self) -> None:
        self._root.bind_all("<KeyPress>", self._on_press)
        self._root.bind_all("<KeyRelease>", self._on_release)

    def stop(self) -> None:
        try:
            self._root.unbind_all("<KeyPress>")
            self._root.unbind_all("<KeyRelease>")
        except tk.TclError:
            pass

    def _on_press(self, event) -> None:
        name = event.keysym.lower()
        job = self._pending_release.pop(name, None)
        if job is not None:
            self._root.after_cancel(job)
        self.handle_press(name)

    def _on_release(self, event) -> None:
        name = event.keysym.lower()
        if name in self._pending_release:
            return
        self._pending_release[name] = self._root.after(
            self._grace_ms, lambda: self._finish_release(name)
        )

    def _finish_release(self, name: str) -> None:
        self._pending_release.pop(name, None)
        self.handle_release(name)
