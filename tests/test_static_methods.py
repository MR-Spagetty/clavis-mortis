try:
    import clavis_mortis
except:
    print('failed to import for testing')
from os.path import join as path_join


def test_texture_path_get():
    correct_path = path_join(
        clavis_mortis.path_to_inside, "tiles", "inside", "ground", "Planks.png"
        )
    given_path = clavis_mortis.Texture.get_path("cm:inside.ground.planks")
    assert correct_path == given_path


def test_texture_path_get_invalid():
    errored = True
    try:
        clavis_mortis.Texture.get_path("cm:aaaaaaaahhhh")
    except KeyError:
        errored = True
    assert errored


def test_level_path_get():
    correct_path = path_join(
        clavis_mortis.path_to_inside, "levels", "demo.json"
        )
    given_path = clavis_mortis.Level.get_path("cm:demo")
    assert correct_path == given_path


def test_level_path_get_invalid():
    errored = True
    try:
        clavis_mortis.Level.get_path("cm:aaaaaaaahhhh")
    except KeyError:
        errored = True
    assert errored
