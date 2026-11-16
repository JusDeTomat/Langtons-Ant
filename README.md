Langton's Ant
Description

A real-time visual simulation of Langton's Ant, a two-dimensional cellular automaton based on a simple set of rules.

The ant moves on an infinite grid of black and white cells. At each step, it follows two rules:

On a white cell, it turns 90° clockwise, changes the cell to black, and moves forward.
On a black cell, it turns 90° counterclockwise, changes the cell to white, and moves forward.

Despite these simple rules, the simulation produces complex patterns and eventually generates a repeating structure known as the highway.

The project is implemented in Python using Pygame, with a focus on smooth rendering, camera controls, and simulation performance.

Instructions

Requirements: Python 3.10+ and Pygame.

Install the dependency:

bash
pip install pygame


Run the simulation:

bash
python main.py

Controls
Key / Input	Action
SPACE	Pause / Resume
UP	Increase simulation speed
DOWN	Decrease simulation speed
MOUSE WHEEL	Zoom in / out
LEFT CLICK + DRAG	Move the camera
F	Toggle camera follow
A	Fit all visited cells into view
C	Change color theme
N	Advance one simulation step
R	Reset simulation
H	Hide / Show interface
+ / -	Zoom in / out
ESC	Quit
Features
Real-time simulation with adjustable speed.
12 speed levels, from 1 to 100,000 steps per second.
Smooth camera movement and automatic ant tracking.
Dynamic zoom with mouse wheel and keyboard controls.
Automatic view adjustment to fit all visited cells.
Cell coloring based on their age.
Glowing ant with directional indicator.
Live statistics: steps, speed, black cells, visited cells, zoom, and FPS.
Dark interface with a gradient background and visual effects.
Project structure
text
.
├── main.py          # Main application, rendering and controls
├── ant.py           # Ant logic and simulation
├── enum_color.py    # Cell color definitions
└── README.md

Technical details
Parameter	Value
Language	Python
Graphics library	Pygame
Window resolution	1180 × 780
Target FPS	60
Maximum steps per frame	4,000
Simulation speeds	1 – 100,000 steps/s
Minimum zoom	1.0
Maximum zoom	96.0

The rendering system uses viewport culling to draw only visible cells. Camera movement and zoom are interpolated to ensure smooth transitions. Cell colors are determined by their age using precomputed color lookup tables.

Resources
Langton's Ant: https://en.wikipedia.org/wiki/Langton%27s_ant
Pygame documentation: https://www.pygame.org/docs/
Python documentation: https://docs.python.org/3/
