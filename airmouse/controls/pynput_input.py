from typing import Mapping, Optional

from .commands import Command
from .keyboard_input import KeyboardInput


class PynputKeyboardInput(KeyboardInput):
    """Global key capture (works while any app is focused).

    Note: pynput's listener aborts the process on recent macOS, so use
    TkKeyboardInput there.
    """

    def __init__(self, bindings: Mapping[str, Command]):
        super().__init__(bindings)
        from pynput import keyboard

        self._keyboard = keyboard
        self._listener = keyboard.Listener(
            on_press=lambda key: self.handle_press(self._name(key)),
            on_release=lambda key: self.handle_release(self._name(key)),
        )

    def _name(self, key) -> Optional[str]:
        """'space' for special keys, lower-case character for normal keys."""
        if isinstance(key, self._keyboard.Key):
            return key.name
        char = getattr(key, "char", None)
        return char.lower() if char else None

    def start(self) -> None:
        self._listener.start()

    def stop(self) -> None:
        self._listener.stop()
