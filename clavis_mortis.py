#!/usr/bin/python3
# clavis_mortis.py
# MR-Spagetty

try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget,
        QSizePolicy, QGridLayout, QPushButton,
        QTabWidget, QLabel, QDialog, QLineEdit,
        QVBoxLayout, QMessageBox
    )
    from PySide6.QtGui import QIcon, QPixmap, QScreen
    from PySide6.QtCore import Qt, QSize, QSizeF, QRect
except ImportError as qt_er:
    raise ImportError("'PySide6' is required to run this game.") from qt_er

try:
    import json
except ImportError as json_er:
    raise ImportError("'json' is required to run this game.") from json_er

try:
    import random
except ImportError as rand_er:
    raise ImportError("'random' is required to run this game.") from rand_er

try:
    import os
    import sys
except ImportError as error:
    raise ImportError("WHAT HAVE YOU DONE") from error

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


class CodeDialog(QDialog):
    def __init__(self, lock: "Lock"):
        """a dialog for the player to enter a code into to unlock a lock

        Args:
            lock (Lock): the lock for the code to be attempted with
        """
        super(CodeDialog, self).__init__()
        self.lock = lock
        self.entry = QLineEdit()
        self.submit = QPushButton("Submit")
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.entry)
        self.layout().addWidget(self.submit)
        self.submit.clicked.connect(self.on_submit)

    def on_submit(self, *args):
        """function to verify the code entered by the user
        """
        if self.entry.text() == self.lock.code:
            self.lock.state = False
            QMessageBox(
                QMessageBox.Icon.Information, "Accepted",
                "teh code you entered was correct\nthe lock is now unlocked",
                QMessageBox.Ok
            ).exec()
        else:
            self.lock.increment_failures()
            QMessageBox(
                QMessageBox.Icon.Warning, "Denied",
                "teh code you entered was incorrect\nthe lock is still locked",
                QMessageBox.Ok
            ).exec()
        self.close()


class Lock:
    chars = "0123456789"

    def __init__(self):
        self.state = True
        self.code = None
        self.fails = 0

        self.randomize_code()

    def randomize_code(self):
        self.code = random.sample(Lock.chars, 6)

    def increment_failures(self):
        self.fails += 1
        if self.fails >= 3:
            self.fails = 0
            self.randomize_code()

    def get_state(self):
        return self.state


class Player:
    texture = Texture(Texture.get_path("cm:player"))

    def __init__(self, game: "Game", level: "Level",
                 layer: str, x: int, y: int,
                 dialog_label: QLabel, update_function: "function"
                 ):
        self.layer = layer
        self.x = x
        self.y = y
        self.dialog_label = dialog_label
        self.update = update_function
        self.code_dialog = CodeDialog()

    def move(self, direction: str, ammount: int = 1):
        match direction:
            case "up" | "north":
                self.y += ammount
            case "right" | "east":
                self.y += ammount
            case "down" | "south":
                self.y -= ammount
            case "left" | "west":
                self.x -= ammount
        self.reset_dialog()
        self.update()

    def teleport(self, layer: str, x: int, y: int):
        self.layer, self.x, self.y = layer, x, y
        self.reset_dialog()
        self.update()

    def dialog(self, dialog: str):
        self.dialog_label.setText(dialog)

    def reset_dialog(self):
        self.dialog_label.setText("")


class Tile:
    def __init__(
        self, texture: Texture,
        function: str = None,
        function_arg: str = None,
        locked: bool = False,
        lock: Lock = None
            ):
        self.texture = QIcon(texture)
        self.function = function
        self.function_arg = function_arg
        self.lock = lock
        if locked:
            self.lock.get_state()
        self.locked = locked

    def attempt_entry(self, player: Player, direction_attempted: str):
        match self.function:
            case None:
                player.move(direction_attempted)
            case "door":
                layer, x, y = self.function_arg.split(",")
                player.teleport(layer, int(x[:-1]), int(y[:-1]))
            case "through-door":
                player.move(direction_attempted, 2)
            case "code":
                CodeDialog(self.lock).exec()
            case "wall":
                player.dialog("That is a wall.")


class Level:
    def __init__(self, path: str | bytes):
        self.textures = {}
        self.map = {}
        self.codes = {}
        with open(path, 'r') as level:
            data = json.load(level)
        self.load_textures(data["tile_key"])

    def load_textures(self, tile_key: dict):
        for key, texture_id in tile_key.items():
            self.textures[key] = Texture(Texture.get_path(texture_id))

    def construct_walls(self, walls_data: list, layers: dict):
        for wall in walls_data:
            start, end = wall.split(":")
            s_lay, s_x, s_y = start.split(",")
            e_lay, e_x, e_y = end.split(",")
            if s_lay != e_lay:
                raise ValueError(
                    f"start and end points of wall ({wall}) "
                    "are not in same layer"
                    )
            elif s_lay not in self.map:
                self.map[s_lay] = [[None * 16] * 16]
            for x in range(min(int(s_x), int(e_x)),
                           max(int(s_x), int(e_x)) + 1):
                for y in range(min(int(s_y), int(e_y)),
                               max(int(s_y), int(e_y)) + 1):
                    self.map[s_lay][y][x] = Tile(
                        self.textures[layers[s_lay][y][x]],
                        "wall"
                    )

    def assemble_functional_tiles(self, functions: dict, layers: dict):
        for location, data in functions.items():
            lay, x, y = location.split(",")
            if lay not in self.map:
                self.map[lay] = [[None * 16] * 16]
            self.map[lay][y][x] = Tile(
                self.textures[layers[lay][y][x]],
                data["type"],
            )

    def construct_map(self, layers: dict):
        pass


class Game:
    def __init__(self):
        pass
