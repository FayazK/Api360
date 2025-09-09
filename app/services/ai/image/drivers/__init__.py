"""Image drivers package.

Concrete provider drivers (e.g., Gemini, Imagen, DALL·E, Replicate) should
live in this package and subclass `ImageDriver` from
`app.services.ai.image.factory`. Drivers should register themselves with the
factory by calling `ImageDriverFactory.register(DriverClass)` — typically at
module import time.
"""

from . import gemini_nano_banana  # noqa: F401  # ensure registration side-effect
from . import imagen_driver  # noqa: F401
from . import replicate_driver  # noqa: F401

__all__ = [
    "gemini_nano_banana",
    "imagen_driver",
    "replicate_driver",
]
