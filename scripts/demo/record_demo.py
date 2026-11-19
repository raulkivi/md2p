#!/usr/bin/env python3
"""Record the README demo GIFs in a real xterm on a private Xvfb display.

Usage: python3 scripts/demo/record_demo.py [scene ...] [--out-dir img]

Needs Xvfb, xterm, xdotool, ffmpeg, less and mc. Each scene runs with a
throwaway HOME, so nothing from your shell setup appears in the frames.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import List

from demo_commands import COLS, FPS, FRAME, ROWS, demo_env, gif_args, record_args, xdotool_args, xterm_args, xvfb_args
from demo_fixtures import demo_files, md2p_shim, write_tree
from demo_scenes import SCENES, TYPE_DELAY_MS, Pause, Scene

REPO = Path(__file__).resolve().parents[2]
TOOLS = ('Xvfb', 'xterm', 'xdotool', 'ffmpeg', 'less', 'mc')


def free_display() -> str:
    n = 90
    while Path(f'/tmp/.X11-unix/X{n}').exists() or Path(f'/tmp/.X{n}-lock').exists():
        n += 1
    return f':{n}'


def wait_for(predicate, timeout: float, what: str) -> None:
    deadline = time.monotonic() + timeout
    while not predicate():
        if time.monotonic() > deadline:
            raise RuntimeError(f'timed out waiting for {what}')
        time.sleep(0.1)


def play(scene: Scene, env: dict) -> None:
    for step in scene.steps:
        if isinstance(step, Pause):
            time.sleep(step.seconds)
        else:
            subprocess.run(xdotool_args(step, TYPE_DELAY_MS), env=env, check=True)


def record_scene(scene: Scene, out_dir: Path) -> Path:
    with tempfile.TemporaryDirectory(prefix='md2p-demo-') as tmp:
        home = Path(tmp)
        files = demo_files(readme=(REPO / 'README.md').read_text(encoding='utf-8'))
        files['bin/md2p'] = md2p_shim(str(REPO / 'md2p.py'))
        write_tree(home, files, executable={'bin/md2p'})

        display = free_display()
        env = demo_env(str(home), str(home / 'bin'), display, os.environ)
        procs: List[subprocess.Popen] = []
        try:
            procs.append(subprocess.Popen(xvfb_args(display, FRAME), stderr=subprocess.DEVNULL))
            wait_for(lambda: Path(f'/tmp/.X11-unix/X{display[1:]}').exists(), 10, 'Xvfb')
            procs.append(subprocess.Popen(xterm_args(COLS, ROWS), env=env, cwd=home / 'notes'))
            subprocess.run(['xdotool', 'search', '--sync', '--onlyvisible', '--class', 'xterm'],
                           env=env, check=True, stdout=subprocess.DEVNULL, timeout=10)
            time.sleep(0.5)  # let bash print its first prompt

            master = home / f'{scene.name}.mp4'
            recorder = subprocess.Popen(record_args(display, FRAME, FPS, str(master)),
                                        stdin=subprocess.PIPE)
            try:
                play(scene, env)
            finally:
                recorder.communicate(b'q', timeout=30)  # ffmpeg finishes the file on "q"

            out_dir.mkdir(parents=True, exist_ok=True)
            gif = out_dir / f'{scene.name}.gif'
            subprocess.run(gif_args(str(master), FPS, str(gif)), check=True)
            return gif
        finally:
            for proc in reversed(procs):
                proc.terminate()
                proc.wait(timeout=10)


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('scenes', nargs='*', metavar='scene',
                        help=f"default: all ({', '.join(SCENES)})")
    parser.add_argument('--out-dir', type=Path, default=REPO / 'img')
    args = parser.parse_args(argv)
    unknown = [name for name in args.scenes if name not in SCENES]
    if unknown:
        parser.error(f"unknown scene: {', '.join(unknown)}")

    missing = [tool for tool in TOOLS if shutil.which(tool) is None]
    if missing:
        print(f"missing tools: {', '.join(missing)}", file=sys.stderr)
        return 1

    for name in args.scenes or list(SCENES):
        gif = record_scene(SCENES[name], args.out_dir)
        print(f'{gif}  {gif.stat().st_size // 1024} KB')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
