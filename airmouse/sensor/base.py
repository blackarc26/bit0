from abc import ABC, abstractmethod
from typing import Callable, List

from .sample import Sample

SampleListener = Callable[[Sample], None]


class SensorSource(ABC):
    """Anything that produces Samples (serial, BLE, replay file, simulator).

    Consumers subscribe a callback. Callbacks run on the source's own
    thread, so they must be thread-safe.
    """

    def __init__(self) -> None:
        self._listeners: List[SampleListener] = []

    def subscribe(self, listener: SampleListener) -> None:
        self._listeners.append(listener)

    def _publish(self, sample: Sample) -> None:
        for listener in self._listeners:
            listener(sample)

    @property
    @abstractmethod
    def connected(self) -> bool:
        ...

    @abstractmethod
    def start(self) -> None:
        ...

    @abstractmethod
    def stop(self) -> None:
        ...
