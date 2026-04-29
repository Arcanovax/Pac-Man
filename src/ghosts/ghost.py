"""Compatibility re-exports for ghost classes.

Other modules import ghost classes from `src.ghosts.ghost`. After
refactoring the implementations live in separate modules, keep this
module as a thin layer that re-exports them so existing imports
continue to work.
"""

from .ghost_base import (
    Ghost,
    STATE_CHASE,
    STATE_FRIGHTENED,
    STATE_EATEN,
)

from .blinky import Blinky
from .pinky import Pinky
from .inky import Inky
from .clyde import Clyde

__all__ = [
    'Ghost',
    'Blinky',
    'Pinky',
    'Inky',
    'Clyde',
    'STATE_CHASE',
    'STATE_FRIGHTENED',
    'STATE_EATEN',
]
