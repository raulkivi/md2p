from demo_scenes import MAX_SECONDS, SCENES, Key, Pause, Scene, Type, scene_seconds


def test_scene_seconds_adds_typing_keys_and_pauses():
    scene = Scene('x', 'alt', (Type('abcd'), Key('Return'), Pause(1.5)))

    assert scene_seconds(scene, type_delay_ms=100, key_seconds=0.2) == 0.4 + 0.2 + 1.5


def test_every_scene_fits_the_gif_budget():
    for scene in SCENES.values():
        assert scene_seconds(scene) <= MAX_SECONDS, scene.name


def test_scenes_are_keyed_by_name_and_have_alt_text():
    assert set(SCENES) == {'quick-start', 'hidden-characters', 'pager', 'midnight-commander'}
    for name, scene in SCENES.items():
        assert scene.name == name
        assert len(scene.alt) > 40


def test_every_scene_ends_on_a_hold_so_the_result_stays_readable():
    for scene in SCENES.values():
        last = scene.steps[-1]
        assert isinstance(last, Pause) and last.seconds >= 2, scene.name


def test_midnight_commander_scene_views_showcase_then_note():
    steps = SCENES['midnight-commander'].steps
    # ~/notes lists "..", README.md, note.md, showcase.md in C collation.
    first_view = steps.index(Key('F3'))
    assert sum(1 for s in steps[:first_view] if s == Key('Down')) == 3
    rest = steps[first_view + 1:]
    assert rest.index(Key('q')) < rest.index(Key('Up')) < rest.index(Key('F3'))
