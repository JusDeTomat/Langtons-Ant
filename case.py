from enum_color import Color


class Case():
    def __init__(self, pos=(0, 0)):
        self.color = Color.WHITE
        self.pos = tuple(pos)
        self.visit = False
        self.last = -1

    def get_pos(self):
        return self.pos
