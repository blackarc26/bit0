from typing import Callable, Dict

from ..config import AppConfig
from .base import MotionMapper

MapperFactory = Callable[[AppConfig], MotionMapper]

_FACTORIES: Dict[str, MapperFactory] = {}


def register_mapper(name: str):
    """Decorator registering a factory under `name`."""

    def decorator(factory: MapperFactory) -> MapperFactory:
        _FACTORIES[name] = factory
        return factory

    return decorator


def create_mapper(name: str, config: AppConfig) -> MotionMapper:
    try:
        factory = _FACTORIES[name]
    except KeyError:
        known = ", ".join(sorted(_FACTORIES))
        raise ValueError(f"Unknown motion mode '{name}'. Known: {known}") from None
    return factory(config)
