try:
    from clavis_mortis import Coordinate
except:
    print('failed to import for testing')


def test_call():
    """checking that the Coordinate object correctly retuns when called on
    construction
    """
    assert Coordinate("1,0x,0y")() == ("1", 0, 0)


def test_call_after():
    """checking that the Coordinate object correctly retuns when called
    after construction
    """
    coord = Coordinate("1,0x,0y")
    assert coord() == ("1", 0, 0)


def test_lower_boundary_in():
    """checking that no error occurs when values are inside the lower boundary
    """
    errored = False
    try:
        Coordinate("1,1x,1y", 0)
    except Exception:
        errored = True
    assert not errored


def test_lower_boundary_on():
    """checking that no error occurs when values are on the lower boundary
    """
    errored = False
    try:
        Coordinate("1,0x,0y", 0)
    except Exception:
        errored = True
    assert not errored


def test_lower_boundary_out():
    """checking that a ValueError occurs when values are outside the lower
    boundary
    """
    correctly_errored = False
    try:
        Coordinate("1,-1x,-1y", 0)
    except Exception as err:
        correctly_errored = type(err) is ValueError
    assert correctly_errored


def test_upper_boundary_in():
    """checking that no error occurs when values are inside the upper boundary
    """
    errored = False
    try:
        Coordinate("1,14x,14y", 0, 15)
    except Exception:
        errored = True
    assert not errored


def test_upper_boundary_on():
    """checking that no error occurs when values are on the upper boundary
    """
    errored = False
    try:
        Coordinate("1,15x,15y", 0, 15)
    except Exception:
        errored = True
    assert not errored


def test_upper_boundary_out():
    """checking that a ValueError occurs when values are outside the upper
    boundary
    """
    correctly_errored = False
    try:
        Coordinate("1,16x,16y", 0, 15)
    except Exception as err:
        correctly_errored = type(err) is ValueError
    assert correctly_errored


def test_invalid_coordinate():
    """checking that a TypeError occurs when values are not valid ints
    """
    correctly_errored = False
    try:
        Coordinate("1,ax,by", 0, 15)
    except Exception as err:
        correctly_errored = type(err) is TypeError
    assert correctly_errored
