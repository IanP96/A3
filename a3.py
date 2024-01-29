"""
Code for Farm Game (assignment 3 of CSSE1001).
By Ian Pinto
"""
import tkinter as tk
from tkinter import filedialog  # For masters task
from typing import Callable, Union, Optional
from a3_support import *
from model import *
from constants import *

__author__ = 'Ian Pinto'

BANNER_PATH = 'images/header.png'
TOTAL_WIDTH = FARM_WIDTH + INVENTORY_WIDTH
NEXT_DAY = 'Next day'
GROUND_IMG_NAMES = {GRASS: 'grass', SOIL: 'soil', UNTILLED: 'untilled_soil'}
GAME_TITLE = 'Farm Game'
PLANT_CLASSES = {
    'Potato Seed': PotatoPlant, 'Kale Seed': KalePlant,
    'Berry Seed': BerryPlant
}
INFO_BAR_STATS = ['Day:', 'Money:', 'Energy:']
KEY_DIRECTIONS = {'w': UP, 'a': LEFT, 's': DOWN, 'd': RIGHT}


class InfoBar(AbstractGrid):
    """
    The view at the bottom of the screen showing the day, money and energy.
    """

    def __init__(self, master: tk.Tk | tk.Frame) -> None:
        """
        Creates an appropriately sized info bar.

        Args:
            master (tk.Tk): The root window where the view will be located.
        """
        super().__init__(master, (2, 3), (TOTAL_WIDTH, INFO_BAR_HEIGHT))

    def redraw(self, day: int, money: int, energy: int) -> None:
        """
        Redraw the info bar to show the given day, money and energy.

        Args:
            day (int): The current day in-game.
            money (int): The player's remaining money.
            energy (int): The player's remaining energy.
        """
        self.clear()
        labels = [INFO_BAR_STATS, [str(day), f'${money}', str(energy)]]
        for row in range(2):
            font = HEADING_FONT if not row else None
            for column in range(3):
                label = labels[row][column]
                self.annotate_position((row, column), label, font)


class FarmView(AbstractGrid):
    """
    The view showing the farm and its ground, player and plants.
    """

    def __init__(
            self, master: tk.Tk | tk.Frame, dimensions: tuple[int, int],
            size: tuple[int, int], **kwargs
    ) -> None:
        """
        Initialises the farm view.

        Args:
            master (tk.Tk | tk.Frame): The master window or frame.
            dimensions (tuple[int, int]): The dimensions of the view in
                the form `(rows, columns)`.
            size: The size of the view (in pixels) in the form
                `(width, height)`
            **kwargs: Optional keyword arguments passed to
                AbstractGrid.__init__.
        """
        super().__init__(master, dimensions, size, **kwargs)
        self._cache = {}

    def redraw(
            self, ground: list[str], plants: dict[tuple[int, int], Plant],
            player_position: tuple[int, int], player_direction: str
    ) -> None:
        """
        Draws the images for the ground, plants and player.

        Args:
            ground (str): The list of ground tile types as strings.
            plants (dict[tuple[int, int], Plant]): A dictionary mapping
                positions in the form `(row, column)` to the plant at that
                position.
            player_position (tuple[int, int]): The position of the player in
                the form `(row, column)`.
            player_direction (str): The player's current direction
                ('up', 'down', 'left' or 'right').
        """
        self.clear()

        # Ground images
        for row, tiles in enumerate(ground):
            for column, tile in enumerate(tiles):
                path = f'{GROUND_IMG_NAMES[tile]}.png'
                self.add_image(path, (row, column))

        # Plant images
        for position, plant in plants.items():
            self.add_image(f'{get_plant_image_name(plant)}', position)

        # Player image
        self.add_image(f'player_{player_direction}.png', player_position)

    def add_image(self, path: str, position: tuple[int, int]) -> None:
        """
        Adds an image at the given grid position.

        Args:
            path (str): The path of the image file. Don't include 'images/'
                before the path.
            position (tuple[int, int]): The position to draw the image in the
                form `(row, column)`.
        """
        image = get_image(
            f'images/{path}', self.get_cell_size(), self._cache
        )
        self.create_image(*self.get_midpoint(position), image=image)


class ItemView(tk.Frame):
    """
    A view showing inventory info, prices and buy/sell buttons for a single
    item.
    """

    def __init__(
            self, master: tk.Frame, item_name: str, amount: int,
            select_command: Optional[Callable[[str], None]] = None,
            sell_command: Optional[Callable[[str], None]] = None,
            buy_command: Optional[Callable[[str], None]] = None
    ) -> None:
        """
        Initialises the item view.

        Args:
            master (tk.Frame): The frame that the item view will be packed in.
            item_name (str): The name of the item in this view.
            amount (int): The amount of the item the player has.
            select_command ((str) -> None | None): The command to call when
                this view is selected.
            sell_command ((str) -> None | None): The command to call when
                selling an item.
            buy_command ((str) -> None | None): The command to call when buying
                an item.
        """

        # Setting the view's appearance
        super().__init__(
            master, width=INVENTORY_WIDTH, height=round(FARM_WIDTH / 6),
            relief=tk.RAISED, borderwidth=2
        )

        # Label
        self._item_name = item_name
        self._label = tk.Label(self)
        self._label.pack(side=tk.LEFT)

        # Buttons
        if item_name in BUY_PRICES:
            self._buy_button = tk.Button(
                self, text='Buy', command=lambda: buy_command(self._item_name)
            )
            self._buy_button.pack(side=tk.LEFT)
        else:
            self._buy_button = None
        self._sell_button = tk.Button(
            self, text='Sell', command=lambda: sell_command(self._item_name)
        )
        self._sell_button.pack(side=tk.LEFT)

        # Binding the select handler
        for widget in self, self._label:
            widget.bind(
                '<Button-1>', lambda _: select_command(self._item_name)
            )

        self.update(amount)

    def update(self, amount: int, selected: bool = False) -> None:
        """
        Updates the view's colour and widgets according to the current game
        state.

        Args:
            amount (int): The amount of the item the player has.
            selected (bool): `True` if this view is selected, `False`
                otherwise. Defaults to `False`.
        """

        # Label text
        label_text = (
            f'{self._item_name}: {amount}\n'
            f'Sell price: ${SELL_PRICES[self._item_name]}\n'
            f'Buy price: ${BUY_PRICES.get(self._item_name, "N/A")}'
        )
        self._label.config(text=label_text)

        # Background colours
        if not amount:
            colour = INVENTORY_EMPTY_COLOUR
        elif selected:
            colour = INVENTORY_SELECTED_COLOUR
        else:
            colour = INVENTORY_COLOUR
        for widget in self, self._label:
            widget.config(bg=colour)
        if self._buy_button is not None:
            self._buy_button.config(highlightbackground=colour)
        self._sell_button.config(highlightbackground=colour)

    def get_item_name(self) -> str:
        """
        Returns the name of this view's associated item.
        """
        return self._item_name


class FarmGame:
    """
    The controller for Farm Game.
    """

    def __init__(self, master: tk.Tk, map_file: str) -> None:
        """
        Initialises the Farm Game controller.

        The window title is set, and the title banner, farm view, info bar,
        item views and next day button are created and positioned
        appropriately.

        Args:
            master (tk.Tk): The root window to run the game in.
            map_file (str): The path of the map to play on.
        """
        self._master = master
        self._master.title(GAME_TITLE)
        self._master.bind('<KeyPress>', self.handle_keypress)
        self._model = FarmModel(map_file)
        self._cache = {}

        # Title banner
        banner = get_image(
            BANNER_PATH, (TOTAL_WIDTH, BANNER_HEIGHT), self._cache
        )
        # Using Label here since tk.Canvas failed on Gradescope
        self._title = tk.Label(
            self._master, width=TOTAL_WIDTH, height=BANNER_HEIGHT, image=banner
        )
        self._title.pack(side=tk.TOP)

        # Next day button
        tk.Button(
            self._master, text=NEXT_DAY, command=self.next_day
        ).pack(side=tk.BOTTOM)

        # Info bar
        self._info_bar = InfoBar(self._master)
        self._info_bar.pack(side=tk.BOTTOM)

        # Farm view
        self._farm_view = FarmView(
            self._master, self._model.get_dimensions(),
            (FARM_WIDTH, FARM_WIDTH)
        )
        self._farm_view.pack(side=tk.LEFT)

        # Item view
        self._item_frame = tk.Frame(
            self._master, width=INVENTORY_WIDTH, height=FARM_WIDTH
        )
        self._item_views = []
        for item in ITEMS:
            item_view = ItemView(
                self._item_frame, item, self.get_amount_of(item),
                self.select_item,
                self.sell_item, self.buy_item
            )
            self._item_views.append(item_view)
            item_view.pack(side=tk.TOP, expand=tk.TRUE, fill=tk.BOTH)
        self._item_frame.pack(side=tk.TOP, expand=tk.TRUE, fill=tk.BOTH)

        self.redraw()

    def redraw(self) -> None:
        """
        Redraws the farm view, info bar and item views according to the current
        game state.
        """

        # Info bar
        self._info_bar.redraw(
            self._model.get_days_elapsed(),
            self._model.get_player().get_money(),
            self._model.get_player().get_energy()
        )

        # Farm view
        self._farm_view.redraw(
            self._model.get_map(), self._model.get_plants(),
            self._model.get_player_position(),
            self._model.get_player_direction()
        )

        # Item views
        for item_view in self._item_views:
            item_name = item_view.get_item_name()
            item_view.update(
                self.get_amount_of(item_name),
                item_name == self._model.get_player().get_selected_item()
            )

    def next_day(self) -> None:
        """
        Starts a new day and redraws the views appropriately.
        """
        self._model.new_day()
        self.redraw()

    def handle_keypress(self, event: tk.Event) -> None:
        """
        Handles a key press from the user and performs the appropriate actions
        (player movement, tilling/untilling soil, planting, harvesting

        Args:
            event (tk.Event): The event to handle.
        """
        key = event.keysym.lower()  # Converting the key to lowercase to
        # account for caps lock/shift
        position = self._model.get_player_position()

        match key:

            # Movement
            case 'w' | 'a' | 's' | 'd':
                self._model.move_player(KEY_DIRECTIONS[key])

            # Tilling/untilling soil
            case 't':
                self._model.till_soil(position)
            case 'u':
                self._model.untill_soil(position)

            # Planting
            case 'p':
                selection = self._model.get_player().get_selected_item()
                if (
                        self._model.get_map()[position[0]][position[1]] != SOIL
                        or selection not in SEEDS
                ):
                    return
                amount = self.get_amount_of(selection)
                if not amount:
                    return
                plant = PLANT_CLASSES[selection]()
                if self._model.add_plant(position, plant):
                    self._model.get_player().remove_item((selection, 1))

            # Harvesting/removing plants
            case 'h':
                harvest_result = self._model.harvest_plant(position)
                if harvest_result:
                    self._model.get_player().add_item(harvest_result)
            case 'r':
                self._model.remove_plant(position)

        self.redraw()

    def select_item(self, item_name: str) -> None:
        """
        Selects one of the in-game items.

        Args:
            item_name (str): The name of the item to select.
        """
        self._model.get_player().select_item(item_name)
        self.redraw()

    def buy_item(self, item_name: str) -> None:
        """
        Buys an item if the player has enough money.

        Args:
            item_name (str): The name of the item to buy.
        """
        self._model.get_player().buy(item_name, BUY_PRICES[item_name])
        self.redraw()

    def sell_item(self, item_name: str) -> None:
        """
        Sells an item if the player has it in their inventory.

        Args:
            item_name (str): The name of the item to sell.
        """
        self._model.get_player().sell(item_name, SELL_PRICES[item_name])
        self.redraw()

    def get_amount_of(self, item_name: str) -> int:
        """
        Returns the amount of the item in the player's inventory.

        Args:
            item_name (str): The name of the item.
        """
        return self._model.get_player().get_inventory().get(item_name, 0)


def play_game(root: tk.Tk, map_file: str) -> None:
    """
    Instantiates the controller and runs the game window for Farm Game.

    Args:
        root (tk.Tk): The root window to run the game in.
        map_file (str): The path of the map to play on.
    """
    controller = FarmGame(root, map_file)
    root.mainloop()


def main() -> None:
    """
    Runs Farm Game by calling the play_game function.
    """
    root = tk.Tk()
    play_game(root, 'maps/map1.txt')


if __name__ == '__main__':
    main()
