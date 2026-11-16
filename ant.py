from enum import Enum
from case import Case
from enum_color import Color


class Direction(Enum):
    N = (0, 1)
    E = (1, 0)
    S = (0, -1)
    W = (-1, 0)


DIR = [Direction.N, Direction.E, Direction.S, Direction.W]
VEC = [d.value for d in DIR]


class Ant:
    def __init__(self):
        self.pos = (0, 0)
        self.prev = self.pos
        self.d = 1
        self.grid = {self.pos: Case(self.pos)}
        self.steps = 0
        self.black = 0
        self.visited = 0

    @property
    def direction(self):
        return DIR[self.d]

    def update(self):
        case = self.grid[self.pos]
        if case.color is Color.BLACK:
            case.color = Color.WHITE
            self.d = (self.d + 1) & 3
            self.black -= 1
        else:
            case.color = Color.BLACK
            self.d = (self.d - 1) & 3
            self.black += 1
        if case.last < 0:
            self.visited += 1
        case.last = self.steps
        case.visit = True
        dx, dy = VEC[self.d]
        self.prev = self.pos
        self.pos = (self.pos[0] + dx, self.pos[1] + dy)
        if self.pos not in self.grid:
            self.grid[self.pos] = Case(self.pos)
        self.steps += 1
        return case
