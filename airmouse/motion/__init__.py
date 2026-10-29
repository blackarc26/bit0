"""Motion mappers. Importing this package registers the built-in ones.

To add a new mapper: create a module, subclass MotionMapper, and decorate a
factory with @register_mapper("name"). Then import it below.
"""

from .base import MotionMapper
from .registry import create_mapper, register_mapper

from . import gyro, tilt  # noqa: F401  (imported for registration)

__all__ = ["MotionMapper", "create_mapper", "register_mapper"]
