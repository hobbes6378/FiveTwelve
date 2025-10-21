"""
Nathanael Davidson

CS-211 
2025-10-20

The game state and logic (model component) of 512, 
a game based on 2048 with a few changes. 
This is the 'model' part of the model-view-controller
construction plan.  It must NOT depend on any
particular view component, but it produces event 
notifications to trigger view updates. 
"""

from game_element import GameElement, GameEvent, EventKind
from typing import List, Optional
import random

# Configuration constants
GRID_SIZE = 4

class Vec():
    """
    A Vec is an (x,y) or (row, column) pair that
    represents distance along two orthogonal axes.
    Interpreted as a position, a Vec represents
    distance from (0,0).  Interpreted as movement,
    it represents distance from another position.
    Thus we can add two Vecs to get a Vec.
    """
    #Fixme:  We need a constructor, and __add__ method, and __eq__.
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __add__(self, other: "Vec") -> "Vec":
        return Vec(self.x + other.x, self.y + other.y)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vec):
            return NotImplemented
        return self.x == other.x and self.y == other.y


class Tile(GameElement):
    """A slidy numbered thing."""

    def __init__(self, pos: Vec, value: int):
        super().__init__()
        self.row = pos.x
        self.col = pos.y
        self.value = value

    def __repr__(self):
        """Not like constructor --- more useful for debugging"""
        return f"Tile[{self.row},{self.col}]:{self.value}"

    def __str__(self):
        return str(self.value)
    
    def __eq__(self, other: "Tile") -> bool: # type: ignore[override]
        return self.value == other.value
    
    def move_to(self, new_pos: Vec):
        self.row = new_pos.x
        self.col = new_pos.y
        self.notify_all(GameEvent(EventKind.tile_updated, self))

    def merge(self, other: Optional["Tile"]):
        # This tile incorporates the value of the other tile
        assert not other is None
        self.value = self.value + other.value
        self.notify_all(GameEvent(EventKind.tile_updated, self))
        # The other tile has been absorbed.  Resistance was futile.
        other.notify_all(GameEvent(EventKind.tile_removed, other))

    


class Board(GameElement):
    """
    The game grid.  Inherits 'add_listener' and 'notify_all'
    methods from game_element.GameElement so that the game
    can be displayed graphically.
    """

    def __init__(self, rows: int = 4, cols: int =4):
        super().__init__()
        self.rows = rows
        self.cols = cols
        self.tiles = [[None for _ in range(cols)] for _ in range(rows)]
    
    def __getitem__(self, pos: Vec) -> Optional["Tile"]:
        return self.tiles[pos.x][pos.y]

    def __setitem__(self, pos: Vec, tile: Optional["Tile"]):
        self.tiles[pos.x][pos.y] = tile # type: ignore[override]

    def has_empty(self) -> bool:
        """Is there at least one grid element without a tile?"""
        return len(self._empty_positions()) > 0
    
    def _empty_positions(self) -> list[Vec]:
        """
        Return a list of positions of None values,
        i.e., unoccupied spaces.
        """
        empties: list[Vec] = []
        for row in range(len(self.tiles)):
            for col in range(len(self.tiles[row])):
                if not self.tiles[row][col]:
                    empties.append(Vec(row, col))
        return empties

    def place_tile(self, value: Optional[int] = None):
        """Place a tile on a randomly chosen empty square."""
        empties = self._empty_positions()
        assert len(empties) > 0
        choice = random.choice(empties)
        row, col = choice.x, choice.y
        if value is None:
            # 0.1 probability of 4
            if random.random() < 0.1:
                value = 4
            else:
                value = 2
        new_tile = Tile(Vec(row, col), value)
        self.tiles[row][col] = new_tile # type: ignore[override]
        self.notify_all(GameEvent(EventKind.tile_created, new_tile))

    def score(self) -> int:
        """
        Calculate a score from the board.
        (Differs from classic 1024, which calculates score
        based on sequence of moves rather than state of
        board.
        """
        total = 0
        as_list = self.to_list()
        for row in as_list:
            for item in row:
                total += item
        return total

    def to_list(self) -> List[List[int]]:
        """
        Test scaffolding: represent each Tile by its
        integer value and empty positions as 0
        """
        result: List[List[int]] = []
        for row in self.tiles:
            row_values: list[int] = []
            for col in row:
                if col is None:
                    row_values.append(0)
                else:
                    row_values.append(col.value)
            result.append(row_values)
        return result
    
    def from_list(self, values: List[List[int]]):
        """
        Test scaffolding: set board tiles to the
        given values, where 0 represents an empty space.
        """
        for i in range(len(values)):
            for j in range(len(values[i])):
                self.tiles[i][j] = Tile(Vec(i, j), values[i][j]) if values[i][j] > 0 else None # type: ignore[override]
    
    def in_bounds(self, pos: Vec) -> bool:
        """Is position (pos.x, pos.y) a legal position on the board?"""
        return not(pos.x < 0 or pos.y < 0 or pos.x > len(self.tiles)-1 or pos.y > len(self.tiles[0])-1)
    
    def slide(self, pos: Vec,  dir: Vec):
        """
        Slide tile at row,col (if any)
        in direction (dx,dy) until it bumps into
        another tile or the edge of the board.
        """
        if self[pos] is None:
            return
        while True:
            new_pos = pos + dir
            if not self.in_bounds(new_pos):
                break
            if self[new_pos] is None:
                self._move_tile(pos, new_pos)
            elif self[pos] == self[new_pos]:
                self[pos].merge(self[new_pos]) # type: ignore[method nonsense from optional]
                self._move_tile(pos, new_pos)
                break  # Stop moving when we merge with another tile
            else:
                # Stuck against another tile
                break
            pos = new_pos

    def _move_tile(self, old_pos: Vec, new_pos: Vec):
        self[old_pos].move_to(new_pos) # type: ignore[method nonsense from optional]
        self[new_pos] = self[old_pos]
        self[old_pos] = None

    def left(self):
        self._move(Vec(0, -1), Vec(1, 1))

    def right(self):
        self._move(Vec(0, 1), Vec(1, -1))

    def up(self):
        self._move(Vec(-1, 0), Vec(1, 1))

    def down(self):
        self._move(Vec(1, 0), Vec(-1, 1))

    def _move(self, dir: Vec, adjustment: Vec):
        adjusted_rows = self.tiles[::adjustment.x]
        for row in adjusted_rows:
            adjusted_col = row[::adjustment.y]
            for cell in adjusted_col:
                if not cell is None:
                    self.slide(Vec(cell.row, cell.col), dir)