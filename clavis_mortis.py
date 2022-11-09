#!/usr/bin python3
# clavis_mortis.py
# MR-Spagetty

try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget,
        QSizePolicy, QGridLayout, QPushButton,
        QTabWidget, QLabel, QDialog, QLineEdit,
        QVBoxLayout, QHBoxLayout, QMessageBox
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

try:
    app = QApplication()
except RuntimeError:
    print("So you imported me...")

# chcecking if the game is bundled into an executable
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
elif __file__:
    application_path = os.path.dirname(__file__)
file_location = os.path.dirname(os.path.abspath(__file__))

# Checking that the user is using a version of python that has match cases
if sys.version_info < (3, 10, 0):
    raise RuntimeError(
        "You must be using a version of python that is 3.10.0 or newer"
        )

# the maximum size of the display grid so i don't haev to repeat it
global MAX_SIZE
MAX_SIZE = 16


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
                "the code you entered was correct\nthe lock is now unlocked",
                QMessageBox.Ok
            ).exec()
        else:
            self.lock.increment_failures()
            QMessageBox(
                QMessageBox.Icon.Warning, "Denied",
                "the code you entered was incorrect\nthe lock is still locked",
                QMessageBox.Ok
            ).exec()
        self.close()


class Lock:
    chars = "0123456789"

    def __init__(self):
        """creates a lock to be used by functional tiles such as doors
        """
        self.state = True
        self.code = None
        self.fails = 0

        self.randomize_code()

    def randomize_code(self):
        """randomizes the code
        """
        self.code = random.sample(Lock.chars, 6)

    def increment_failures(self):
        """if the player inputs the code in wrong this method will keep track
        of the number of times the player gets the code wrong a number of
        times beyond a threshold the code will be randomized
        """
        self.fails += 1
        if self.fails >= 3:
            self.fails = 0
            self.randomize_code()

    def get_state(self):
        """gets the state of the lock

        Returns:
            bool: the state of the lock
        """
        return self.state


class Coordinate:
    def __init__(
        self, value: str = "1,0x,0y",
        min_val: int = 0, max_val: int = 15
            ):
        """simple class to make handeling of coordinates easier

        Args:
            value (str, optional): the layer, x, y values of the coordinate in
            the form "<str layer>,<int x>x,<int y>y". Defaults to "1,0x,0y".
            min_val (int, optional): the minimum possible value
            for an x or y coordinate. Defaults to 0.
            max_val (int, optional): the maximum possible value
            for an x or y coordinate. Defaults to 15.
        """
        self.min_val = min_val
        self.max_val = max_val

        self.layer, x, y = value.split(",")

        self.x = self.coord_int(x[:-1])
        self.y = self.coord_int(y[:-1])

    def coord_int(self, value: str):
        """function to turn the x and y coordinates given to it into valid
        intigers.

        Args:
            value (str): the value to chack the validity of and convert.

        Raises:
            TypeError: if the given value is not an int.
            ValueError: if the given value is not within the range of the
            Coordinate object.

        Returns:
            int: the validated and converted value.
        """
        NUMS = "-0123456789"
        if all(char in NUMS for char in value):
            new_val = int(value)
        else:
            raise TypeError("the given value is not a valid coord_int")
        # check that the value is within the range of the Coordinate object
        if (self.min_val <= new_val <= self.max_val):
            return new_val
        else:
            raise ValueError(
                "the given value does not fall within this coordinate's range"
                )

    def __call__(self) -> tuple[str, int, int]:
        """Returns the coordinates when the objecte is called as a function

        Returns:
            tuple: a tuple of the layer, x, and y coordinates stored within
            the object
        """
        return (self.layer, self.x, self.y)


class Player:
    texture = Texture(Texture.get_path("cm:player"))

    def __init__(self, game: "Game", level: "Level",
                 layer: str, x: int, y: int,
                 update_function: "function"
                 ):
        self.layer = layer
        self.x = x
        self.y = y
        self.update = update_function
        
        self.update()

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
        self.update()

    def teleport(self, new_coord: Coordinate):
        self.layer, self.x, self.y = new_coord()
        self.update()

    def dialog(self, dialog: str):
        QMessageBox(
            QMessageBox.Icon.NoIcon, "Dialog", dialog
            ).exec()


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
                if self.locked:
                    CodeDialog(self.lock).exec()
                else:
                    player.teleport(Coordinate(self.function_arg))
            case "through-door":
                player.move(direction_attempted, 2)
            case "code":
                player.dialog(
                    ""
                )
            case "wall":
                player.dialog("That is a wall.")


class Level:
    def __init__(self, game: "Game", path: str | bytes):
        self.textures = {}
        self.map = {}
        self.locks = {}
        with open(path, 'r') as level:
            data = json.load(level)

        # load all the textures needed by the level
        self.load_textures(data["tile_key"])

        # seperate the level data from the texture data
        level_data = data["level"]
        # seperate the layers to their own variable for easier referencing
        layers = level_data["layers"]

        self.start = Coordinate(level_data["start"])
        end = Coordinate(level_data["end"])

        self.construct_walls(level_data["walls"])

        game.player.teleport(self.start)

    def load_textures(self, tile_key: dict):
        for key, texture_id in tile_key.items():
            self.textures[key] = Texture(Texture.get_path(texture_id))

    def fill_layer(self, layer_id: str):
        self.map[layer_id] = [[None * MAX_SIZE] * MAX_SIZE]

    def setup_end(self,
                  end_coord: Coordinate,
                  layers: dict):
        pass

    def construct_walls(self, walls_data: list, layers: dict):
        for wall in walls_data:
            start, end = wall.split(":")
            s_lay, s_x, s_y = Coordinate(start)()
            e_lay, e_x, e_y = Coordinate(end)()
            if s_lay != e_lay:
                raise ValueError(
                    f"start and end points of wall ({wall}) "
                    "are not in same layer"
                    )
            elif s_lay not in self.map:
                self.fill_layer(s_lay)
            for x in range(min(s_x, e_x),
                           max(s_x, e_x) + 1):
                for y in range(min(s_y, e_y),
                               max(s_y, e_y) + 1):
                    self.map[s_lay][y][x] = Tile(
                        self.textures[layers[s_lay][y][x]],
                        "wall"
                    )

    def assemble_functional_tiles(self, functions: dict, layers: dict):
        global MAX_SIZE
        for location, data in functions.items():
            lay, x, y = Coordinate(location)()
            # filling in the layer if it doent already exist
            if lay not in self.map:
                self.fill_layer(lay)

            # deciding the arg naem depending on hte function type
            match data["type"]:
                case "door":
                    arg_name = "goes_to"
                case "dialog":
                    arg_name = "text"
                case other:
                    arg_name = "arg"

            # sorting out the lock
            lock_id = data.get("lock_id", None)
            if lock_id not in self.locks:
                self.locks[lock_id] = Lock()

            # creating the tile
            self.map[lay][y][x] = Tile(
                self.textures[layers[lay][y][x]],
                data["type"], data.get(arg_name, None),
                data.get("locked", False), self.locks[lock_id]
            )

    def construct_map(self, layers: dict):
        global MAX_SIZE
        for layer_id, layer in layers.items():
            if layer_id not in self.map:
                self.fill_layer(layer_id)
            # itterating through the x and y coords the map
            for y in range(MAX_SIZE):
                for x in range(MAX_SIZE):
                    # creating the tile
                    if self.map[layer_id][y][x] is None:
                        self.map[layer_id][y][x] = Tile(
                            Texture(
                                self.textures[layer[y][x]]
                                )
                        )


class Game:
    def __init__(self):
        self.displays = {
            y: {} for y in range(MAX_SIZE)
        }
        self.level = None
        self.player = None

    def add_display_ref(self, display: QPushButton, y: int, x: int):
        self.displays[y][x] = display

    def update_displays(self):
        """updates the tile displays to show the correct texture
        """
        layer = self.player.layer
        for y in range(MAX_SIZE):
            for x in range(MAX_SIZE):
                self.displays[y][x].setIcon(
                    self.level.map[layer][y][x].texture
                )
        self.displays[self.player.y][self.player.x].setIcon(Player.texture)

    def create_player(self, location: Coordinate):
        """creates the player at the given location

        Args:
            location (Coordinate): the location to create the player at
        """
        self.player = Player(
            self, self.level, *location(),
            self.update_displays
            )


class GameWindow(QMainWindow):
    def __init__(self):
        super(GameWindow, self).__init__()
        self.setCentralWidget(QTabWidget())

        self.centralWidget().addTab(QWidget(), "Menu")

        self.game = Game()

        self.game_display_layout = QGridLayout()
        self.game_display_layout.setContentsMargins(0, 0, 0, 0)
        self.game_display_layout.setSpacing(0)
        game_tab = QWidget()
        game_tab.setLayout(QHBoxLayout())

        game_tab.layout().addWidget(QWidget())
        game_display_layout_widget = QWidget()
        game_display_layout_widget.setLayout(self.game_display_layout)
        game_tab.layout().addWidget(game_display_layout_widget)
        game_tab.layout().addWidget(QWidget())

        self.centralWidget().addTab(game_tab, "Layer 1")

        self.screen().geometryChanged.connect(self.on_window_size_changed)
        display_height_width = self.screen().geometry().height()//17
        self.displays_size = QSize(display_height_width, display_height_width)

        self.setup_displays()

    def setup_displays(self):
        global MAX_SIZE
        grid = self.game_display_layout
        for row in range(MAX_SIZE):
            for column in range(MAX_SIZE):
                button = QPushButton()

                button.setFlat(True)
                button.setFixedSize(self.displays_size)
                button.setIconSize(self.displays_size)
                grid.addWidget(button, row, column)
                self.game.add_display_ref(button, row, column)

    def change_displays(self):
        pass

    def on_window_size_changed(self, new_geo: QRect):
        new_dimensions = new_geo.height()//17
        print(new_geo.height()//17)
        self.displays_size.setWidth(new_dimensions)
        self.displays_size.setHeight(new_dimensions)
        grid = self.game_display_layout
        for row in range(MAX_SIZE):
            for column in range(MAX_SIZE):
                button = QPushButton()

                button.setFlat(True)
                button.setFixedSize(self.displays_size)
                button.setIconSize(self.displays_size)
                grid.addWidget(button, row, column)
                self.game.add_display_ref(button, row, column)


if __name__ == "__main__":
    window = GameWindow()
    window.show()
    app.exec()
