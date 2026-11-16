import math
import pygame
from ant import Ant
from enum_color import Color

WIN_SIZE = (1180, 780)
FPS = 60
SPEEDS = [1, 2, 5, 10, 30, 100, 300, 1000, 3000, 10000, 30000, 100000]
START_SPEED = 5
MAX_STEPS_FRAME = 4000
LUT_N = 46
Z_MIN, Z_MAX = 1.0, 96.0

TEXT = (226, 231, 246)
DIM = (126, 134, 164)
AMBER = (255, 200, 90)


def lerp(a, b, t):
    return (int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t))


def fmt(n):
    return f"{n:,}".replace(",", " ")


def line_cells(a, b):
    """Cases traversées entre a et b (Bresenham), pour peindre sans trous."""
    x0, y0 = a
    x1, y1 = b
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        yield (x0, y0)
        if (x0, y0) == (x1, y1):
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


class Theme:
    def __init__(self, name, hot, mid, base, ghost, bg_top, bg_bot, ant):
        self.name = name
        self.hot, self.mid, self.base, self.ghost = hot, mid, base, ghost
        self.bg_top, self.bg_bot, self.ant = bg_top, bg_bot, ant
        self.grid = lerp(lerp(bg_top, bg_bot, 0.5), (255, 255, 255), 0.05)
        self.black, self.white = [], []
        dim_mid = tuple(int(c * 0.55) for c in mid)
        for k in range(LUT_N):
            t = k / (LUT_N - 1)
            if t < 0.4:
                self.black.append(lerp(hot, mid, t / 0.4))
            else:
                self.black.append(lerp(mid, base, (t - 0.4) / 0.6))
            self.white.append(lerp(dim_mid, ghost, t ** 0.7))


THEMES = [
    Theme("Ice", (255, 255, 255), (176, 182, 200), (96, 102, 122),
          (34, 36, 44), (13, 14, 17), (24, 25, 30), (255, 208, 90)),
]


def make_vignette():
    n = 64
    v = pygame.Surface((n, n), pygame.SRCALPHA)
    for y in range(n):
        for x in range(n):
            dx = (x - (n - 1) / 2) / ((n - 1) / 2)
            dy = (y - (n - 1) / 2) / ((n - 1) / 2)
            d = min(1.0, math.hypot(dx, dy) / 1.25)
            v.set_at((x, y), (0, 0, 0, int(150 * d ** 2.2)))
    return v


def build_background(size, theme, vignette):
    w, h = size
    bg = pygame.Surface((w, h))
    for y in range(h):
        pygame.draw.line(bg, lerp(theme.bg_top, theme.bg_bot, y / max(1, h - 1)),
                         (0, y), (w, y))
    bg.blit(pygame.transform.smoothscale(vignette, (w, h)), (0, 0))
    return bg


def make_font(names, size, bold=False):
    return pygame.font.SysFont(names, size, bold=bold)


class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Langton's Ant")
        pygame.display.set_mode(WIN_SIZE, pygame.RESIZABLE)
        sans = "inter,segoeui,helveticaneue,helvetica,arial,dejavusans"
        mono = "jetbrainsmono,firacode,menlo,consolas,dejavusansmono,couriernew,monospace"
        self.f_title = make_font(sans, 17, True)
        self.f_small = make_font(sans, 13)
        self.f_small_b = make_font(sans, 13, True)
        self.f_mono = make_font(mono, 14, True)
        self.clock = pygame.time.Clock()
        self.vignette = make_vignette()
        self.glows = {}
        self.bg = None
        self.theme_idx = 0
        self.theme = THEMES[0]
        self.speed_idx = START_SPEED
        self.paused = False
        self.follow = True
        self.show_ui = True
        self.dragging = False


        self.layout = (frozenset(), (0, 0), 1)
        self.edit = True
        self.painting = False
        self.paint_color = Color.BLACK
        self.last_cell = None

        self.reset()
        self.edit = True
        self.paused = True
        self.follow = False

    def reset(self):
        self.ant = Ant.from_layout(*self.layout)
        self.acc = 0.0
        self.cx = self.tx = self.ant.pos[0] + 0.5
        self.cy = self.ty = self.ant.pos[1] + 0.5
        self.z = self.tz = 14.0

    def launch(self):
        """Éditeur -> simulation."""
        self.layout = self.ant.export()
        self.ant = Ant.from_layout(*self.layout)
        self.acc = 0.0
        self.edit = False
        self.painting = False
        self.dragging = False
        self.paused = False
        self.follow = True

    def open_editor(self):
        """Simulation -> éditeur (on retrouve la carte de départ)."""
        self.ant = Ant.from_layout(*self.layout)
        self.acc = 0.0
        self.edit = True
        self.painting = False
        self.dragging = False
        self.paused = True
        self.follow = False

    @property
    def sps(self):
        return SPEEDS[self.speed_idx]

    def ant_visual_pos(self):
        a = self.ant
        f = self.acc if (self.sps <= 60 and not self.paused) else 1.0
        if self.sps <= 60 and self.paused:
            f = 1.0
        f = f * f * (3 - 2 * f)
        return (a.prev[0] + (a.pos[0] - a.prev[0]) * f,
                a.prev[1] + (a.pos[1] - a.prev[1]) * f)

    def screen_to_cell(self, pos):
        W, H = pygame.display.get_surface().get_size()
        ox = W / 2 - self.cx * self.z
        oy = H / 2 + self.cy * self.z
        return (math.floor((pos[0] - ox) / self.z),
                math.floor((oy - pos[1]) / self.z))

    def fit(self):
        pts = [c.pos for c in self.ant.grid.values()
               if c.last >= 0 or c.color is Color.BLACK]
        pts.append(self.ant.pos)
        minx = min(p[0] for p in pts)
        maxx = max(p[0] for p in pts)
        miny = min(p[1] for p in pts)
        maxy = max(p[1] for p in pts)
        W, H = pygame.display.get_surface().get_size()
        w, h = maxx - minx + 1, maxy - miny + 1
        self.tx = (minx + maxx + 1) / 2
        self.ty = (miny + maxy + 1) / 2
        self.tz = max(Z_MIN, min(Z_MAX, W * 0.86 / w, H * 0.8 / h))
        self.follow = False

    def pan(self, rel):
        self.cx -= rel[0] / self.z
        self.cy += rel[1] / self.z
        self.tx, self.ty = self.cx, self.cy

    def handle(self, event):
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.KEYDOWN:
            k = event.key
            if k == pygame.K_ESCAPE:
                return False
            elif k == pygame.K_TAB:
                if self.edit:
                    self.launch()
                else:
                    self.open_editor()
            elif k in (pygame.K_RETURN, pygame.K_KP_ENTER) and self.edit:
                self.launch()
            elif k == pygame.K_a:
                self.fit()
            elif k == pygame.K_c:
                self.theme_idx = (self.theme_idx + 1) % len(THEMES)
                self.theme = THEMES[self.theme_idx]
                self.bg = None
            elif k == pygame.K_h:
                self.show_ui = not self.show_ui
            elif k in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                self.tz = min(Z_MAX, self.tz * 1.25)
            elif k in (pygame.K_MINUS, pygame.K_KP_MINUS):
                self.tz = max(Z_MIN, self.tz / 1.25)
            elif self.edit:
                self.edit_key(k)
            else:
                self.sim_key(k)
        elif event.type == pygame.MOUSEWHEEL:
            self.tz = max(Z_MIN, min(Z_MAX, self.tz * 1.18 ** event.y))
        elif self.edit:
            self.edit_mouse(event)
        else:
            self.sim_mouse(event)
        return True

    def sim_key(self, k):
        if k == pygame.K_SPACE:
            self.paused = not self.paused
        elif k == pygame.K_UP:
            self.speed_idx = min(self.speed_idx + 1, len(SPEEDS) - 1)
        elif k == pygame.K_DOWN:
            self.speed_idx = max(self.speed_idx - 1, 0)
        elif k == pygame.K_f:
            self.follow = not self.follow
        elif k == pygame.K_r:
            self.reset()
        elif k == pygame.K_n:
            self.paused = True
            self.ant.update()
            self.acc = 0.0

    def sim_mouse(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.dragging = True
            self.follow = False
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.pan(event.rel)

    def edit_key(self, k):
        if k == pygame.K_p:
            self.ant.place(self.screen_to_cell(pygame.mouse.get_pos()))
        elif k == pygame.K_t:
            self.ant.rotate(1)
        elif k == pygame.K_x:
            self.ant = Ant.from_layout((), self.ant.pos, self.ant.d)

    def paint_to(self, cell):
        start = self.last_cell if self.last_cell is not None else cell
        for p in line_cells(start, cell):
            self.ant.set_color(p, self.paint_color)
        self.last_cell = cell

    def edit_mouse(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button in (1, 3):
                self.paint_color = Color.BLACK if event.button == 1 else Color.WHITE
                self.painting = True
                self.last_cell = None
                self.paint_to(self.screen_to_cell(event.pos))
            elif event.button == 2:
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button in (1, 3):
                self.painting = False
                self.last_cell = None
            elif event.button == 2:
                self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.painting:
                cell = self.screen_to_cell(event.pos)
                if cell != self.last_cell:
                    self.paint_to(cell)
            elif self.dragging:
                self.pan(event.rel)

    def step_frame(self, dt):
        if self.edit:
            keys = pygame.key.get_pressed()
            mx = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
            my = keys[pygame.K_UP] - keys[pygame.K_DOWN]
            if mx or my:
                sp = 600 / self.z * dt
                self.tx += mx * sp
                self.ty += my * sp
        elif not self.paused:
            self.acc += dt * self.sps
            n = int(self.acc)
            self.acc -= n
            for _ in range(min(n, MAX_STEPS_FRAME)):
                self.ant.update()
        if self.follow and not self.edit:
            vx, vy = self.ant_visual_pos()
            self.tx, self.ty = vx + 0.5, vy + 0.5
        k = 1 - math.exp(-dt * 7)
        if not self.dragging:
            self.cx += (self.tx - self.cx) * k
            self.cy += (self.ty - self.cy) * k
        self.z += (self.tz - self.z) * (1 - math.exp(-dt * 10))
        if abs(self.tz - self.z) < 0.01:
            self.z = self.tz

    def glow(self, size):
        key = (self.theme_idx, size)
        if key not in self.glows:
            R = 64
            s = pygame.Surface((2 * R, 2 * R), pygame.SRCALPHA)
            col = self.theme.ant
            for r in range(R, 0, -1):
                a = int(210 * (1 - r / R) ** 2.3)
                pygame.draw.circle(s, (*col, a), (R, R), r)
            self.glows[key] = pygame.transform.smoothscale(s, (size, size))
        return self.glows[key]


    def draw(self):
        screen = pygame.display.get_surface()
        W, H = screen.get_size()
        if self.bg is None or self.bg.get_size() != (W, H):
            self.bg = build_background((W, H), self.theme, self.vignette)
        screen.blit(self.bg, (0, 0))

        th, ant, z = self.theme, self.ant, self.z
        ox = W / 2 - self.cx * z
        oy = H / 2 + self.cy * z
        x0 = math.floor(self.cx - W / (2 * z)) - 1
        x1 = math.ceil(self.cx + W / (2 * z)) + 1
        y0 = math.floor(self.cy - H / (2 * z)) - 1
        y1 = math.ceil(self.cy + H / (2 * z)) + 1

        BLACK = Color.BLACK

        if z >= 10 or (self.edit and z >= 5):
            for i in range(x0, x1 + 1):
                X = int(ox + i * z)
                pygame.draw.line(screen, th.grid, (X, 0), (X, H))
            for j in range(y0, y1 + 2):
                Y = int(oy - j * z)
                pygame.draw.line(screen, th.grid, (0, Y), (W, Y))

        grid = ant.grid
        cells = []
        if (x1 - x0 + 1) * (y1 - y0 + 1) < len(grid):
            for j in range(y0, y1 + 1):
                for i in range(x0, x1 + 1):
                    c = grid.get((i, j))
                    if c is not None and (c.last >= 0 or c.color is BLACK):
                        cells.append((c, i, j))
        else:
            for c in grid.values():
                if c.last < 0 and c.color is not BLACK:
                    continue
                i, j = c.pos
                if x0 <= i <= x1 and y0 <= j <= y1:
                    cells.append((c, i, j))

        steps = ant.steps
        black_lut, white_lut = th.black, th.white
        gap = 1 if z >= 6 else 0
        radius = int(z * 0.2) if z >= 12 else 0
        for c, i, j in cells:
            age = steps - c.last
            bl = age.bit_length()
            idx = bl * 2
            if bl > 1:
                idx += (age >> (bl - 2)) & 1
            if idx >= LUT_N:
                idx = LUT_N - 1
            col = (black_lut if c.color is BLACK else white_lut)[idx]
            xa = int(ox + i * z)
            xb = int(ox + (i + 1) * z)
            ya = int(oy - (j + 1) * z)
            yb = int(oy - j * z)
            r = (xa + gap, ya + gap, xb - xa - gap, yb - ya - gap)
            if radius:
                pygame.draw.rect(screen, col, r, border_radius=radius)
            else:
                screen.fill(col, r)


        if self.edit and pygame.mouse.get_focused():
            i, j = self.screen_to_cell(pygame.mouse.get_pos())
            xa = int(ox + i * z)
            xb = int(ox + (i + 1) * z)
            ya = int(oy - (j + 1) * z)
            yb = int(oy - j * z)
            pygame.draw.rect(screen, th.ant, (xa, ya, xb - xa, yb - ya), 1)

        vx, vy = self.ant_visual_pos()
        px = ox + (vx + 0.5) * z
        py = oy - (vy + 0.5) * z
        gs = max(32, int(z * 6) // 8 * 8)
        screen.blit(self.glow(gs), (px - gs / 2, py - gs / 2))
        if z >= 6:
            inset = max(1, int(z * 0.14))
            body = pygame.Rect(int(px - z / 2 + inset), int(py - z / 2 + inset),
                               int(z - 2 * inset), int(z - 2 * inset))
            pygame.draw.rect(screen, th.ant, body, border_radius=int(z * 0.3))
            dx, dy = ant.direction.value
            pygame.draw.circle(screen, (255, 255, 255),
                               (int(px + dx * z * 0.2), int(py - dy * z * 0.2)),
                               max(1, int(z * 0.13)))
        else:
            pygame.draw.circle(screen, th.ant, (int(px), int(py)), max(2, int(z * 0.8)))

        if self.show_ui:
            self.draw_hud(screen, W, H)
        else:
            self.draw_badges(screen, W)

    def panel(self, w, h, radius=14):
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(s, (12, 14, 26, 205), s.get_rect(), border_radius=radius)
        pygame.draw.rect(s, (255, 255, 255, 28), s.get_rect(), 1, border_radius=radius)
        return s

    def pill(self, text, color):
        t = self.f_small_b.render(text, True, color)
        w, h = t.get_width() + 24, t.get_height() + 10
        p = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(p, (12, 14, 26, 210), p.get_rect(), border_radius=h // 2)
        pygame.draw.rect(p, (*color, 160), p.get_rect(), 1, border_radius=h // 2)
        p.blit(t, (12, 5))
        return p

    def draw_badges(self, screen, W):
        x = W - 16
        badges = [(self.theme.name.upper(), self.theme.hot)]
        if self.edit:
            badges.append(("EDITOR", AMBER))
        else:
            if self.follow:
                badges.append(("FOLLOW", self.theme.hot))
            if self.paused:
                badges.append(("PAUSED", AMBER))
        for text, col in badges:
            p = self.pill(text, col)
            x -= p.get_width()
            screen.blit(p, (x, 16))
            x -= 8

    def draw_hud(self, screen, W, H):
        a, th = self.ant, self.theme
        if self.edit:
            rows = [
                ("Mode", "EDITOR"),
                ("Black cells", fmt(a.black)),
                ("Ant", f"{a.pos[0]}, {a.pos[1]}"),
                ("Direction", a.direction.name),
                ("Zoom", f"{self.z:.1f} px"),
                ("FPS", f"{self.clock.get_fps():.0f}"),
            ]
        else:
            rows = [
                ("Steps", fmt(a.steps)),
                ("Speed", f"{fmt(self.sps)} /s"),
                ("Black cells", fmt(a.black)),
                ("Visited cells", fmt(a.visited)),
                ("Zoom", f"{self.z:.1f} px"),
                ("FPS", f"{self.clock.get_fps():.0f}"),
            ]
        pw, ph = 272, 74 + len(rows) * 23 + 30
        p = self.panel(pw, ph)
        p.blit(self.f_title.render("Langton's Ant", True, th.hot), (18, 14))
        p.blit(self.f_small.render("cellular automaton", True, DIM), (18, 36))
        pygame.draw.line(p, (255, 255, 255, 30), (18, 62), (pw - 18, 62))
        y = 72
        for label, value in rows:
            p.blit(self.f_small.render(label, True, DIM), (18, y + 1))
            v = self.f_mono.render(value, True, AMBER if label == "Mode" else TEXT)
            p.blit(v, (pw - 18 - v.get_width(), y))
            y += 23
        if not self.edit:
            n = len(SPEEDS)
            bw = (pw - 36 - (n - 1) * 3) / n
            for k in range(n):
                col = th.hot if k <= self.speed_idx else (255, 255, 255, 34)
                pygame.draw.rect(p, col, (18 + k * (bw + 3), y + 8, bw, 5), border_radius=2)
        screen.blit(p, (16, 16))

        self.draw_badges(screen, W)

        if self.edit:
            help_txt = ("LEFT CLICK paint   |   RIGHT CLICK erase   |   MIDDLE DRAG / arrows move   |   "
                        "wheel zoom   |   P place ant   |   T turn ant   |   X clear   |   "
                        "A fit   |   ENTER start   |   H hide UI")
        else:
            help_txt = ("SPACE pause   |   UP/DOWN speed   |   wheel zoom   |   drag move   |   "
                        "F follow   |   A fit   |   N step   |   R reset   |   "
                        "TAB editor   |   H hide UI")
        t = self.f_small.render(help_txt, True, DIM)
        hp = self.panel(t.get_width() + 32, t.get_height() + 16, 12)
        hp.blit(t, (16, 8))
        screen.blit(hp, ((W - hp.get_width()) // 2, H - hp.get_height() - 14))

    def run(self):
        running = True
        while running:
            dt = min(self.clock.tick(FPS) / 1000, 0.1)
            for event in pygame.event.get():
                if not self.handle(event):
                    running = False
            self.step_frame(dt)
            self.draw()
            pygame.display.flip()
        pygame.quit()


if __name__ == "__main__":
    App().run()