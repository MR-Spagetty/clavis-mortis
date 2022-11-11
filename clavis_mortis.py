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
    from PySide6.QtGui import QIcon, QPixmap, QScreen, QShortcut
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
    # this error here should NEVER be seen if it is you have done something
    # very wrong with your python instalation
    raise ImportError("WHAT HAVE YOU DONE") from error

try:
    app = QApplication()
except RuntimeError:
    # little joke that shouldnt be ever seen
    print("So you imported me...")

# chcecking if the game is bundled into an executable
if getattr(sys, 'frozen', False):
    path_to_exe = os.path.dirname(sys.executable)
elif __file__:
    path_to_exe = os.path.dirname(__file__)
path_to_inside = os.path.dirname(os.path.abspath(__file__))

# Checking that the user is using a version of python that has match cases
if sys.version_info < (3, 10, 0):
    raise RuntimeError(
        "You must be using a version of python that is 3.10.0 or newer"
        )

# the maximum size of the display grid so i don't have to repeat it
global MAX_SIZE
MAX_SIZE = 16


class Texture(QPixmap):
    def __init__(self, path: str | bytes) -> None:
        """the texture to be used by a tile or maybe even the players

        Args:
            path (str | bytes): the path to the texture file
        """
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
            initial_folder = os.path.join(path_to_inside, "tiles")
        else:
            initial_folder = os.path.join(
                path_to_exe, "mods", modid, "tiles"
                )

        with open(os.path.join(initial_folder, "tiles.json")) as reference:
            mod_tile_reference_sheet = json.load(reference)
        texture_path = []
        navigator = mod_tile_reference_sheet.copy()
        # itterating through each part of the texture id in the reference
        # sheet to get the final path
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
        self.setWindowTitle("Enter code")
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
            # you got the code right
            self.lock.state = False
            QMessageBox(
                QMessageBox.Icon.Information, "Accepted",
                "the code you entered was correct\nthe lock is now unlocked",
                QMessageBox.Ok
            ).exec()
        else:
            # you got the code wrong
            reset = self.lock.increment_failures()
            QMessageBox(
                QMessageBox.Icon.Warning, "Denied",
                # the dialog you will get if you failed to enter the code
                # correctly and the code has been randomized
                "the code you entered was incorrect\n"
                "the lock is still locked\n"
                "perhapse i should check the code again" if reset else
                # the dialog you will get if you failed to enter the code
                # correctly and the cdoe has NOT been randomized
                "the code you entered was incorrect\n"
                "the lock is still locked",
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
        self.code = "".join(random.sample(Lock.chars, 6))

    def increment_failures(self):
        """if the player inputs the code in wrong this method will keep track
        of the number of times the player gets the code wrong a number of
        times beyond a threshold the code will be randomized
        """
        self.fails += 1
        if self.fails >= 3:
            self.fails = 0
            self.randomize_code()
            return True
        return False

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

    def __init__(self, game: "Game",
                 layer: str, x: int, y: int,
                 update_function: "function"
                 ):
        """the player, aguably the most important part of the game
        without this object you would not be able to play let alone complete
        the game

        Args:
            game (Game): the game object that created this player
            layer (str): the layer the player is to start on
            x (int): the x coordinate the player is to start at
            y (int): the y coordinate the plaeyr is to start at
            update_function (function): the function the player will run after
            moveing in some way to update the game's displays
        """
        self.game = game
        self.layer = layer
        self.x = x
        self.y = y
        self.update = update_function

    def move(self, direction: str, ammount: int = 1):
        """simply moves the player in the specified direction by the specifed
        number of tiles

        Args:
            direction (str): the direction to move the player
            ammount (int, optional): the number of tiles to move the player.
            Defaults to 1.
        """
        match direction:
            case "up" | "north":
                self.y -= ammount
            case "right" | "east":
                self.x += ammount
            case "down" | "south":
                self.y += ammount
            case "left" | "west":
                self.x -= ammount
        self.update()

    def teleport(self, new_coord: Coordinate):
        """sets the players layer and position to the specified coordinate

        Args:
            new_coord (Coordinate): the position and layer to teleport the
            player to
        """
        self.layer, self.x, self.y = new_coord()
        self.update()

    def dialog(self, dialog: str):
        """prompts the player with a dialog

        Args:
            dialog (str): the message to haev in the dialog prompt
        """
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
        """the humble tile is what a level is made of many of.
        They can come in various textures and functions all you need to do is
        tell them what they are and what they look like

        Args:
            texture (Texture): the texture this tile will show
            function (str, optional): the function this tile will server,
            if None it will do nothing but sit there. Defaults to None.
            function_arg (str, optional): any special argument for this tile
            not applicable to non functional tiles. Defaults to None.
            locked (bool, optional): whether this tile is locked or not, only
            applicable to doors (through and normal). Defaults to False.
            lock (Lock, optional): the lock to lock the door with,
            only applicable to locked doors. Defaults to None.
        """
        self.texture = QIcon(texture)
        self.function = function
        self.function_arg = function_arg
        self.lock = lock
        if lock:
            self.locked = self.lock.get_state
        elif locked:
            self.locked = lambda: True
        else:
            self.locked = lambda: False

    def attempt_entry(self, player: Player, direction_attempted: str):
        """a method to tell the player what to do when the attempt to enter
        this tile

        Args:
            player (Player): the player to give the instruction too
            direction_attempted (str): the direction the player attemted to
            move to get into this tile
        """
        match self.function:
            case None:
                # if the tile is not a special tile it will simply\
                # move the player
                player.move(direction_attempted)
            case "door":
                # if the tile is a door it will first check if it is locked
                if self.locked():
                    # if it is locked it will prompt the player to enter the
                    # code of the lock if applicable otherwise just inform the
                    # user that they are unable to unlock it
                    # (locked from the other side)
                    if self.lock:
                        CodeDialog(self.lock).exec()
                    else:
                        player.dialog("The door is locked from the other side")
                else:
                    # if the door is not locked it will teleport the player to
                    # the appropriate location
                    player.teleport(Coordinate(self.function_arg))
            case "through-door":
                # if the tile is a through door it will first check if it is
                # locked
                if self.locked():
                    # if it is locked it will prompt the player to enter the
                    # code of the lock if applicable otherwise just inform the
                    # user that they are unable to unlock it
                    # (locked from the other side)
                    if self.lock:
                        CodeDialog(self.lock).exec()
                    else:
                        player.dialog("The door is locked from the other side")
                else:
                    # if the through door is not locked it will move the
                    # player to the opposite side to that from which they
                    # approched
                    player.move(direction_attempted, 2)
            case "code":
                # if the tile is a code tile then the player will recieve a
                # little dialog about a note left for someone named John, who
                # appears to be a security risk, that contains the code to a
                # door
                player.dialog(
                    "You find a note, on it is written:\n"
                    "\"John remember the code this time\n"
                    f"code: {player.game.level.locks[self.function_arg].code}"
                    "\"\nMan this John guy is a real security risk"
                )
            case "dialog":
                # if the tile is a dialog tile the player will recieve a
                # dialog contaning the dialog specified for this tile by the
                # level file
                player.dialog(self.function_arg)
            case "wall":
                # if the tile is a wall tile the player will be informed that
                # the obeject they just walked into is a wall
                player.dialog("That is a wall.")
            case "end":
                # if the tile is a end tile the level will end
                player.game.level.end(player.game)


class Level:
    def __init__(self, game: "Game", path: str | bytes):
        """the constructor for any level of the game

        Args:
            game (Game): the game object that this level is being created in
            path (str | bytes): the path to the file for this level
        """
        self.textures = {}
        self.map = {}
        self.locks = {
            None: None, "": None
            }
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

        self.construct_walls(level_data["walls"], layers)
        self.assemble_functional_tiles(level_data["functions"], layers)
        self.construct_map(layers)

        self.setup_end(end, layers)

        game.create_player(self.start)

    def get_path(full_level_id: str):
        """Static method to get the path to the level file
        from the given full level id.

        Args:
            full_level_id (str): the full id of the level

        Returns:
            str: the path to the level file
        """
        modid, level_id = full_level_id.split(':')
        infos = level_id.split('.')
        if modid == "cm":
            initial_folder = os.path.join(path_to_inside, "levels")
        else:
            initial_folder = os.path.join(
                path_to_exe, "mods", modid, "levels"
                )

        with open(os.path.join(initial_folder, "levels.json")) as reference:
            mod_tile_reference_sheet = json.load(reference)
        tile_path = []
        navigator = mod_tile_reference_sheet.copy()
        # itterates through each part of the level id in the reference sheet
        # to get the final path
        for info in infos[:-1]:
            tile_path.append(info)
            navigator = navigator.copy()[info]
        tile_path.append(navigator[infos[-1]])
        return os.path.join(initial_folder, *tile_path)

    def load_textures(self, tile_key: dict):
        """loads all the textures required by the level

        Args:
            tile_key (dict): the textures to be loaded and their keys that
            they will be referenced as when constructing the map
        """
        for key, texture_id in tile_key.items():
            self.textures[key] = Texture(Texture.get_path(texture_id))

    def fill_layer(self, layer_id: str):
        """method to prep a layer to be filled with tiles if it does not
        already exist

        Args:
            layer_id (str): the id of the layer to be preped
        """
        self.map[layer_id] = {y: {} for y in range(16)}

    def setup_end(self,
                  end_coord: Coordinate,
                  layers: dict):
        """sets up the end tile of the map

        Args:
            end_coord (Coordinate): the location that the end tile will be
            placed at
            layers (dict): the data from which the texture for this tile will
            be derived
        """
        lay, x, y = end_coord()
        # creating the tile
        self.map[lay][y][x] = Tile(
            self.textures[layers[lay][y][x]], "end"
        )

    def construct_walls(self, walls_data: list, layers: dict):
        """constructs the walls that are within the level

        Args:
            walls_data (list): a list of the walls in the level
            layers (dict): the data from which the textures for these tiles
            can be derived

        Raises:
            ValueError: if a wall does not start and end on the same layer
        """
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
        """assembles all the functinoal tiles in the level

        Args:
            functions (dict): the functional tiles to setup
            layers (dict): the data from which the textures for these tiles
            can be derived
        """
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
                case "code":
                    arg_name = "lock_id"
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
        """constructs the map as plain tiles with the textures specified in
        the level data

        Args:
            layers (dict): the level data to get the texture keys from
        """
        global MAX_SIZE
        # itterating through each layer in the level data
        for layer_id, layer in layers.items():
            if layer_id not in self.map:
                # setting up layers that do not already exist
                self.fill_layer(layer_id)
            # itterating through the x and y coords the map
            for y in range(MAX_SIZE):
                for x in range(MAX_SIZE):
                    # creating the tile
                    if self.map[layer_id][y].get(x) is None:
                        self.map[layer_id][y][x] = Tile(
                            Texture(
                                self.textures[layer[y][x]]
                                )
                        )

    def end(self, game: "Game"):
        """method for when the player complete the level

        Args:
            game (Game): the game object the level is running in
        """
        if game.demo_mode:
            end_dialog = QMessageBox(
                QMessageBox.Icon.NoIcon, "Level_complete",
                "Congrats you completed the demo",
                QMessageBox.Close
            )
            end_dialog.exec()
            sys.exit()


class Game:
    #     x, y, name
    UP = (0, 1, "up")
    DOWN = (0, -1, "down")
    LEFT = (-1, 0, "left")
    RIGHT = (1, 0, "right")

    def __init__(self, window: QMainWindow, demo_mode: bool = False):
        """constructor class of the game

        Args:
            window (QMainWindow): the window the game is running in
        """
        self.displays = {
            y: {} for y in range(MAX_SIZE)
        }
        self.level = None
        self.player = None

        # adding a reference to the parent window to be used later
        self.window = window

        # storing whether the game is in demo mode
        self.demo_mode = demo_mode

        # creating the up key and binding it to the move method
        self.up_key = QShortcut(window)
        self.up_key.setKey('w')
        self.up_key.activated.connect(lambda: self.move_player(self.UP))

        # creating the down key and binding it to the move method
        self.down_key = QShortcut(window)
        self.down_key.setKey('s')
        self.down_key.activated.connect(lambda: self.move_player(self.DOWN))

        # creating the left key and binding it to the move method
        self.left_key = QShortcut(window)
        self.left_key.setKey('a')
        self.left_key.activated.connect(lambda: self.move_player(self.LEFT))

        # creating the right key and binding it to the move method
        self.right_key = QShortcut(window)
        self.right_key.setKey('d')
        self.right_key.activated.connect(lambda: self.move_player(self.RIGHT))

        # determining the the game is in demo mode and if so running the demo
        # level
        if demo_mode:
            self.load_level("cm:demo")
        else:
            # only a demo has been made at this point in time so you can't
            # play the non demo
            raise RuntimeError("You're not allowed to do that")

    def load_level(self, level_id: str):
        """loads the level with the specified id

        Args:
            level_id (str): the id of the level to load
        """
        level_path = Level.get_path(level_id)
        self.level = Level(self, level_path)

    def add_display_ref(self, display: QPushButton, y: int, x: int):
        """adds a reference ot a display in the window to the game object

        Args:
            display (QPushButton): the display to add a reference to
            y (int): the row the display is on in the display matrix
            x (int): the column the display is on in the display matrix
        """
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
            self, *location(),
            self.update_displays
            )

    def move_player(self, direction: tuple[int, int, str]):
        """method to move the player when a direction key is pressed

        Args:
            direction (tuple): a tuple of the relative coordinates and name of
            the direction from the player in the format (x, y, name)
        """
        if self.window.centralWidget().currentIndex() == 1:
            dir_x, dir_y, dir_name = direction
            x = self.player.x + dir_x  # y coords must be subtracted due
            y = self.player.y - dir_y  # to y = 0 being at the top
            # telling the tile at the location to that the player is
            # attempting to enter the tile in the specified direction
            self.level.map[self.player.layer][y][x].attempt_entry(
                self.player, dir_name
                )

    def start(self):
        """starts the level
        """
        self.player.update()


class GameWindow(QMainWindow):
    def __init__(self, demo_mode: bool = False):
        """the constructor class for the game_window.

        Args:
            demo_mode (bool): _description_
        """
        super(GameWindow, self).__init__()
        self.setCentralWidget(QTabWidget())

        menu_widget = QWidget()
        menu_layout = QVBoxLayout()
        menu_widget.setLayout(menu_layout)

        # creating the start/resume button
        self.start_resume_button = QPushButton()
        # setting the size of the button
        self.start_resume_button.setFixedHeight(80)
        self.start_resume_button.setFixedWidth(300)
        # setting up the text and text size
        self.start_resume_button.setText("Start")
        self.start_resume_button.setStyleSheet("font-size: 70px")
        # binding the button to the pause function
        self.start_resume_button.clicked.connect(
            self.pause
            )
        menu_layout.addWidget(self.start_resume_button)

        # creating a quit button
        quit_button = QPushButton()
        # setting the size of the button
        quit_button.setFixedHeight(80)
        quit_button.setFixedWidth(300)
        # setting up the text and text size
        quit_button.setText("Quit")
        quit_button.setStyleSheet("font-size: 70px")
        # binding the button to quit the game
        quit_button.clicked.connect(
            # this is a lambda function so the exit doesn't accidentally get
            # an exit code
            lambda: sys.exit()
            )
        menu_layout.addWidget(quit_button)

        self.centralWidget().addTab(menu_widget, "Menu")

        # creating the game to run in the window
        self.game = Game(self, demo_mode)

        # creating the pause key and binding it
        pause_key = QShortcut(self)
        pause_key.setKey("esc")
        pause_key.activated.connect(self.pause)

        # creating the layout for the displays
        self.game_display_layout = QGridLayout()
        # making it so that there are no gaps between the tile displays
        self.game_display_layout.setContentsMargins(0, 0, 0, 0)
        self.game_display_layout.setSpacing(0)
        game_tab = QWidget()
        game_tab.setLayout(QHBoxLayout())

        # creating the tab the game will run in
        game_tab.layout().addWidget(QWidget())  # 1*
        game_display_layout_widget = QWidget()
        game_display_layout_widget.setLayout(self.game_display_layout)
        game_tab.layout().addWidget(game_display_layout_widget)
        game_tab.layout().addWidget(QWidget())  # 1*
        # 1*:
        # spacing widgets so that the tile displays dont get pulled appart
        # when the window is stretched horizontally

        # sticking the game tab into the window
        self.centralWidget().addTab(game_tab, "Game")

        # setting up graphical changes required for the winodw being resized
        self.screen().geometryChanged.connect(self.on_window_size_changed)
        display_height_width = self.screen().geometry().height()//17
        self.displays_size = QSize(display_height_width, display_height_width)

        # final game setup
        self.setup_displays()
        # starting the game
        self.game.start()

    def pause(self):
        """method to toggle the pause state of the game
        """
        self.start_resume_button.setText("Resume")
        if self.centralWidget().currentIndex() == 1:
            self.centralWidget().setCurrentIndex(0)
        else:
            self.centralWidget().setCurrentIndex(1)

    def setup_displays(self):
        """method to setup the displays of the window
        """
        global MAX_SIZE
        grid = self.game_display_layout
        # itterating through the grid to make all the required displays
        for row in range(MAX_SIZE):
            for column in range(MAX_SIZE):
                button = QPushButton()

                # creating the display
                button.setFlat(True)
                button.setFixedSize(self.displays_size)
                button.setIconSize(self.displays_size)
                # adding the display to the grid
                grid.addWidget(button, row, column)
                # allowing the game to acces the display
                self.game.add_display_ref(button, row, column)

    def on_window_size_changed(self, new_geo: QRect):
        """method to change the size of the displays when the window size is
        changed

        Args:
            new_geo (QRect): the new window size
        """
        # dividing the new height of the window bvy 17
        # (16 for the tiles + 1 for the tab bar at the top)
        new_dimensions = new_geo.height()//17

        # setting the dislpays_size property to be the enw size
        self.displays_size.setWidth(new_dimensions)
        self.displays_size.setHeight(new_dimensions)

        # iterating through the displays and chanign their sizes to the new
        # size
        for row in range(MAX_SIZE):
            for column in range(MAX_SIZE):
                self.game.displays[row][column].setFixedSize(
                    self.displays_size
                    )
                self.game.displays[row][column].setIconSize(
                    self.displays_size
                    )


if __name__ == "__main__":
    # running the game
    window = GameWindow(True)
    window.show()
    app.exec()
