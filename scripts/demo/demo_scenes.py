"""The README demo scenes: what is typed into the terminal, and the pauses between."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple, Union

TYPE_DELAY_MS = 55
KEY_SECONDS = 0.1
MAX_SECONDS = 20.0


@dataclass(frozen=True)
class Type:
    text: str


@dataclass(frozen=True)
class Key:
    name: str  # an xdotool key name


@dataclass(frozen=True)
class Pause:
    seconds: float


Step = Union[Type, Key, Pause]


@dataclass(frozen=True)
class Scene:
    name: str
    alt: str
    steps: Tuple[Step, ...]


def scene_seconds(scene: Scene, type_delay_ms: int = TYPE_DELAY_MS,
                  key_seconds: float = KEY_SECONDS) -> float:
    total = 0.0
    for step in scene.steps:
        if isinstance(step, Type):
            total += len(step.text) * type_delay_ms / 1000
        elif isinstance(step, Key):
            total += key_seconds
        else:
            total += step.seconds
    return round(total, 6)


def _command(text: str, hold: float) -> Tuple[Step, ...]:
    return (Type(text), Pause(0.4), Key('Return'), Pause(hold))


_SCENES = (
    Scene(
        'quick-start',
        'A terminal runs md2p showcase.md and prints the file styled: a centered '
        'title, bold, italic and inline code, nested lists, a blockquote and a table',
        (Pause(1),) + _command('md2p showcase.md', 6),
    ),
    Scene(
        'hidden-characters',
        'cat note.md shows an ordinary payment note with a total of 95 EUR; md2p '
        'note.md shows the hidden variation selectors and a carriage return that '
        'hid the real total of 9950 EUR, each as a red hex marker',
        (Pause(1),) + _command('cat note.md', 3) + _command('md2p note.md', 6),
    ),
    Scene(
        'pager',
        'cat README.md piped through md2p into less -R: paging down through the '
        'rendered README, then searching for Options',
        (Pause(1),) + _command('cat README.md | md2p | less -R', 2.5)
        + (Key('space'), Pause(2), Key('space'), Pause(2))
        + _command('/Options', 3),
    ),
    Scene(
        'midnight-commander',
        'Midnight Commander with the md2p viewer rule: F3 on showcase.md opens it '
        'formatted in the internal viewer, then F3 on note.md shows its hidden '
        'characters as markers',
        (Pause(1),) + _command('mc', 2)
        + (Key('Down'), Pause(0.4)) * 3
        + (Key('F3'), Pause(3.5), Key('q'), Pause(0.6), Key('Up'), Pause(0.5),
           Key('F3'), Pause(3.5)),
    ),
)

SCENES: Dict[str, Scene] = {scene.name: scene for scene in _SCENES}
