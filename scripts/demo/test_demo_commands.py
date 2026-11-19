from demo_commands import (
    FRAME,
    demo_env,
    gif_args,
    record_args,
    xdotool_args,
    xterm_args,
    xvfb_args,
)
from demo_scenes import Key, Pause, Type


def test_frame_is_80_by_24_cells():
    assert FRAME == (80 * 14, 24 * 28)


def test_xvfb_screen_matches_the_frame():
    args = xvfb_args(':42', (1120, 672))

    assert args[:2] == ['Xvfb', ':42']
    assert '1120x672x24' in args


def test_xterm_fills_the_frame_without_border_or_scrollbar():
    args = xterm_args(80, 24)

    assert args[0] == 'xterm'
    assert '80x24+0+0' in args
    for flag in ('+sb', '-bw', '-b'):
        assert flag in args
    # bash without rc files: the prompt is exactly the PS1 from demo_env.
    assert args[-4:] == ['-e', 'bash', '--norc', '--noprofile']


def test_xdotool_types_text_at_the_given_delay():
    assert xdotool_args(Type('md2p x.md'), delay_ms=55) == [
        'xdotool', 'type', '--delay', '55', 'md2p x.md']


def test_xdotool_presses_keys():
    assert xdotool_args(Key('Return'), delay_ms=55) == ['xdotool', 'key', 'Return']


def test_xdotool_sends_function_keys_by_keycode():
    # By keysym, Xvfb's keymap delivers F3 as Alt+F3 (ESC[1;3R), which mc ignores.
    assert xdotool_args(Key('F3'), delay_ms=55) == ['xdotool', 'key', '69']
    assert xdotool_args(Key('F10'), delay_ms=55) == ['xdotool', 'key', '76']


def test_pause_needs_no_command():
    assert xdotool_args(Pause(1), delay_ms=55) is None


def test_record_args_grab_the_display_without_pointer():
    args = record_args(':42', (1120, 672), fps=10, out='m.mp4')

    assert args[args.index('-f') + 1] == 'x11grab'
    assert args[args.index('-video_size') + 1] == '1120x672'
    assert args[args.index('-draw_mouse') + 1] == '0'
    assert args[args.index('-i') + 1] == ':42.0+0,0'
    assert args[-1] == 'm.mp4'


def test_gif_args_build_a_palette_and_loop():
    args = gif_args('m.mp4', fps=10, out='x.gif')

    vf = args[args.index('-vf') + 1]
    assert vf.startswith('fps=10,')
    assert 'palettegen' in vf and 'paletteuse' in vf
    assert args[args.index('-loop') + 1] == '0'
    assert args[-1] == 'x.gif'


def test_demo_env_isolates_the_session_from_the_user():
    base = {'PATH': '/usr/bin', 'HOME': '/home/someone', 'XDG_CONFIG_HOME': '/x',
            'LESS': '-X', 'PS1': 'someone@host$ '}

    env = demo_env('/tmp/demo', '/tmp/demo/bin', ':42', base)

    assert env == {
        'HOME': '/tmp/demo',
        'PATH': '/tmp/demo/bin:/usr/bin',
        'DISPLAY': ':42',
        'PS1': '$ ',
        'LC_ALL': 'C.UTF-8',
    }
