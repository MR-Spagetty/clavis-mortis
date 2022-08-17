#!/usr/bin/python3
# clavis_mortis.py
# MR-Spagetty

try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget,
        QSizePolicy, QGridLayout, QPushButton,
        QTabWidget
    )
    from PySide6.QtGui import QIcon, QPixmap, QScreen
    from PySide6.QtCore import Qt, QSize, QSizeF, QRect
except ImportError as e:
    raise ImportError("'PySide6' is required to run this game.") from e

try:
    import json
except ImportError as er:
    raise ImportError("'json' is required to run this game.") from er

try:
    import os
    import sys
except ImportError as err:
    raise ImportError("WHAT HAVE YOU DONE") from err

app = QApplication()

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
elif __file__:
    application_path = os.path.dirname(__file__)
file_location = os.path.dirname(os.path.abspath(__file__))


class Texture(QPixmap):
    def __init__(self, path) -> None:
        super(Texture, self).__init__(path)

    def get_path(full_texture_id: str):
        """Static method to get the path to the texture file
        from the given full texture id.

        Args:
            full_texture_id (str): the full id of the texture

        Returns:
            str: the path to the texture file
        """
        modid, texture_id = full_texture_id.split(':')
        infos = texture_id.split('.')
        if modid == "cm":
            initial_folder = os.path.join(application_path, "tiles")
        else:
            initial_folder = os.path.join(file_location, "mods", modid)

        with open(os.path.join(initial_folder, "tiles.json")) as reference:
            mod_tile_reference_sheet = json.load(reference)
        texture_path = []
        navigator = mod_tile_reference_sheet.copy()
        for info in infos[:-1]:
            texture_path.append(info)
            navigator = navigator.copy()[info]
        texture_path.append(navigator[infos[-1]])
        return os.path.join(initial_folder, *texture_path)


class Tile:
    def __init__(self, texture: Texture):
        self.texture = QIcon(texture)


class Level:
    def __init__(self, path: str | bytes):
        pass


class Player:
    def __init__(self):
        pass


class Game:
    def __init__(self):
        pass