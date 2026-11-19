"""Command lines for the demo recorder's external tools. Pure: the driver runs them."""
from __future__ import annotations

from typing import Dict, List, Mapping, Optional, Tuple

from demo_scenes import Key, Step, Type

FONT = 'DejaVu Sans Mono'
FONT_SIZE = 17
CELL = (14, 28)  # pixels per cell at FONT_SIZE, measured under Xvfb
COLS, ROWS = 80, 24
FRAME = (COLS * CELL[0], ROWS * CELL[1])
FPS = 10

Size = Tuple[int, int]


def xvfb_args(display: str, size: Size) -> List[str]:
    return ['Xvfb', display, '-screen', '0', f'{size[0]}x{size[1]}x24', '-nolisten', 'tcp']


def xterm_args(cols: int, rows: int) -> List[str]:
    return [
        'xterm',
        '-fa', FONT, '-fs', str(FONT_SIZE),
        # No border or scrollbar, so the window is exactly cols x rows cells.
        '+sb', '-b', '0', '-bw', '0',
        '-bg', '#0d1117', '-fg', '#e6edf3', '-cr', '#e6edf3',
        '-geometry', f'{cols}x{rows}+0+0',
        '-e', 'bash', '--norc', '--noprofile',
    ]


# By keysym, Xvfb's keymap delivers F-keys with Alt held (F3 arrives as ESC[1;3R) and mc
# ignores them; the evdev keycodes arrive unmodified.
_FUNCTION_KEYCODES = {f'F{n}': str(66 + n) for n in range(1, 11)}


def xdotool_args(step: Step, delay_ms: int) -> Optional[List[str]]:
    if isinstance(step, Type):
        return ['xdotool', 'type', '--delay', str(delay_ms), step.text]
    if isinstance(step, Key):
        return ['xdotool', 'key', _FUNCTION_KEYCODES.get(step.name, step.name)]
    return None


def record_args(display: str, size: Size, fps: int, out: str) -> List[str]:
    return [
        'ffmpeg', '-y', '-loglevel', 'error',
        '-f', 'x11grab', '-video_size', f'{size[0]}x{size[1]}',
        '-framerate', str(fps), '-draw_mouse', '0',
        '-i', f'{display}.0+0,0',
        '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '18', '-pix_fmt', 'yuv420p',
        out,
    ]


def gif_args(input_path: str, fps: int, out: str) -> List[str]:
    # A palette from the frame differences keeps terminal text crisp and the file small.
    vf = (f'fps={fps},split[a][b];'
          '[a]palettegen=stats_mode=diff[p];'
          '[b][p]paletteuse=dither=none:diff_mode=rectangle')
    return ['ffmpeg', '-y', '-loglevel', 'error', '-i', input_path, '-vf', vf, '-loop', '0', out]


def demo_env(home: str, bin_dir: str, display: str, base: Mapping[str, str]) -> Dict[str, str]:
    # Only what the scenes need: nothing from the user's shell setup reaches the frame.
    return {
        'HOME': home,
        'PATH': f"{bin_dir}:{base.get('PATH', '/usr/bin:/bin')}",
        'DISPLAY': display,
        'PS1': '$ ',
        # Byte-order file sorting in mc, so the scene's key presses land on the same file.
        'LC_ALL': 'C.UTF-8',
    }
