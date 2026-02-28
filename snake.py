"""Snake game for Windows CMD terminal. Amiga demo aesthetic."""

import ctypes
import msvcrt
import random
import sys
import time
from collections import deque

BOARD_WIDTH = 40
BOARD_HEIGHT = 20
TICK_SECONDS = 0.1
MAX_QUEUED_TURNS = 3

UP    = (-1,  0)
DOWN  = ( 1,  0)
LEFT  = ( 0, -1)
RIGHT = ( 0,  1)

ARROW_MAP = {'\x48': UP, '\x50': DOWN, '\x4b': LEFT, '\x4d': RIGHT}
WASD_MAP  = {'w': UP, 's': DOWN, 'a': LEFT, 'd': RIGHT}

# ANSI escape codes
R  = '\033[0m'
BO = '\033[1m'
CY = '\033[96m'   # bright cyan
YL = '\033[93m'   # bright yellow
GR = '\033[92m'   # bright green
MG = '\033[95m'   # bright magenta
RD = '\033[91m'   # bright red
WH = '\033[97m'   # bright white
BL = '\033[94m'   # bright blue

# Coloured character lookup used by the renderer
_CHAR = {
    '#': f'{CY}#{R}',
    '@': f'{YL}{BO}@{R}',
    'O': f'{GR}O{R}',
    '*': f'{MG}{BO}*{R}',
}

# Rainbow bars (40 visible chars each)
_BAR_FWD = f'{RD}########{YL}########{GR}########{CY}########{BL}########{R}'
_BAR_REV = f'{BL}########{CY}########{GR}########{YL}########{RD}########{R}'


# ---------------------------------------------------------------------------
# Terminal helpers
# ---------------------------------------------------------------------------

def enable_ansi():
    ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.GetStdHandle(-11)
    mode = ctypes.c_ulong()
    kernel32.GetConsoleMode(handle, ctypes.byref(mode))
    kernel32.SetConsoleMode(handle, mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING)


def hide_cursor():
    sys.stdout.write('\033[?25l')
    sys.stdout.flush()


def show_cursor():
    sys.stdout.write('\033[?25h')
    sys.stdout.flush()


def drain_input():
    while msvcrt.kbhit():
        msvcrt.getwch()


def show_screen(lines):
    """Clear screen and print lines from the top."""
    sys.stdout.write('\033[2J\033[H' + '\n'.join(lines) + '\n')
    sys.stdout.flush()


def show_centered(lines):
    """Clear screen and vertically center lines within the board area."""
    top = max(0, (BOARD_HEIGHT - len(lines)) // 2)
    sys.stdout.write('\033[2J\033[H' + '\n' * top + '\n'.join(lines) + '\n')
    sys.stdout.flush()


def _lpad(text, width=40):
    """Left-padding to center visible text within width chars."""
    return ' ' * max(0, (width - len(text)) // 2)


# ---------------------------------------------------------------------------
# Block-letter SNAKE logo (5 rows x 38 visible chars)
# ---------------------------------------------------------------------------

def _logo_rows():
    S = ['####', '#   ', '####', '   #', '####']
    N = ['#  #', '## #', '# ##', '#  #', '#  #']
    A = [' ## ', '#  #', '####', '#  #', '#  #']
    K = ['#  #', '# # ', '##  ', '# # ', '#  #']
    E = ['####', '#   ', '### ', '#   ', '####']
    rows = []
    for i in range(5):
        content = f'{S[i]} {N[i]} {A[i]} {K[i]} {E[i]}'   # 24 visible chars
        pad = (38 - len(content)) // 2
        rows.append(' ' * pad + content + ' ' * (38 - len(content) - pad))
    return rows


# ---------------------------------------------------------------------------
# Screens
# ---------------------------------------------------------------------------

def startup_screen():
    logo = _logo_rows()
    # All decorative text measured to center within the 40-char bar width
    _sub  = '* C L A S S I C  A R C A D E  G A M E *'  # 39 chars
    _snk  = '>==O>==O>==O>==O>==O>==O>==O>==O>==O>==O'  # 40 chars
    _key  = '[ P R E S S  A N Y  K E Y ]'               # 27 chars
    _ctrl = 'WASD / Arrows to move   Ctrl+Z to quit'    # 38 chars
    lines = [
        '',
        _BAR_FWD,
        _BAR_REV,
        '',
        f'  {GR}{BO}{logo[0]}{R}',
        f'  {GR}{BO}{logo[1]}{R}',
        f'  {GR}{BO}{logo[2]}{R}',
        f'  {GR}{BO}{logo[3]}{R}',
        f'  {GR}{BO}{logo[4]}{R}',
        '',
        _BAR_REV,
        _BAR_FWD,
        '',
        f'{_lpad(_sub)}{YL}{BO}{_sub}{R}',
        '',
        f'{GR}{_snk}{R}',
        '',
        f'{_lpad(_key)}{MG}{BO}{_key}{R}',
        f'{_lpad(_ctrl)}{WH}{_ctrl}{R}',
        '',
    ]
    show_screen(lines)
    drain_input()
    msvcrt.getwch()


def game_over_screen(score):
    """Show score summary. Returns True to restart, False to quit."""
    _title   = '* * *  G A M E   O V E R  * * *'     # 31 chars
    _score_t = f'F I N A L   S C O R E :  {score}'   # 27+ chars
    _opts    = '[ R ] Play Again     [ Q ] Quit'      # 31 chars
    lines = [
        '',
        _BAR_FWD,
        '',
        f'{_lpad(_title)}{RD}{BO}{_title}{R}',
        '',
        f'{_lpad(_score_t)}{WH}F I N A L   S C O R E :{R}  {YL}{BO}{score}{R}',
        '',
        f'{_lpad(_opts)}{GR}{BO}[ R ]{R} Play Again     {MG}{BO}[ Q ]{R} Quit',
        '',
        _BAR_FWD,
        '',
    ]
    show_centered(lines)
    drain_input()
    while True:
        ch = msvcrt.getwch().lower()
        if ch == 'r':
            return True
        if ch in ('q', '\x1a'):
            return False


def goodbye_screen():
    _snk_r = '>==O>==O>==O>==O>==O>==O>==O>==O>==O>==O'  # 40 chars
    _snk_l = 'O==<O==<O==<O==<O==<O==<O==<O==<O==<O==<'  # 40 chars
    _thanks = 'T H A N K S   F O R   P L A Y I N G !'    # 37 chars
    _name   = '>>> S N A K E <<<'                         # 17 chars
    _seeyou = 'S e e   y o u   n e x t   t i m e'        # 33 chars
    lines = [
        '',
        _BAR_FWD,
        _BAR_REV,
        '',
        f'{GR}{_snk_r}{R}',
        '',
        f'{_lpad(_thanks)}{YL}{BO}{_thanks}{R}',
        '',
        f'{_lpad(_name)}{GR}{BO}{_name}{R}',
        '',
        f'{_lpad(_seeyou)}{MG}{_seeyou}{R}',
        '',
        f'{GR}{_snk_l}{R}',
        '',
        _BAR_REV,
        _BAR_FWD,
        '',
    ]
    show_centered(lines)
    time.sleep(2.5)


# ---------------------------------------------------------------------------
# Game logic
# ---------------------------------------------------------------------------

def place_food(snake):
    occupied = set(snake)
    while True:
        pos = (random.randint(1, BOARD_HEIGHT - 2), random.randint(1, BOARD_WIDTH - 2))
        if pos not in occupied:
            return pos


def opposite(d1, d2):
    return d1[0] == -d2[0] and d1[1] == -d2[1]


def read_input(direction_queue, current_direction):
    """Drain keypresses; queue valid turns up to MAX_QUEUED_TURNS. Return quit flag."""
    quit_requested = False
    while msvcrt.kbhit():
        ch = msvcrt.getwch()
        if ch == '\x1a':
            quit_requested = True
            break
        new_dir = None
        if ch in ('\x00', '\xe0'):
            ch2 = msvcrt.getwch()
            new_dir = ARROW_MAP.get(ch2)
        elif ch.lower() in WASD_MAP:
            new_dir = WASD_MAP[ch.lower()]
        if new_dir is not None and len(direction_queue) < MAX_QUEUED_TURNS:
            ref = direction_queue[-1] if direction_queue else current_direction
            if not opposite(new_dir, ref) and new_dir != ref:
                direction_queue.append(new_dir)
    return quit_requested


def render(snake, food, score):
    grid = [
        ['#' if (r == 0 or r == BOARD_HEIGHT - 1 or c == 0 or c == BOARD_WIDTH - 1) else ' '
         for c in range(BOARD_WIDTH)]
        for r in range(BOARD_HEIGHT)
    ]
    fr, fc = food
    grid[fr][fc] = '*'
    for i, (r, c) in enumerate(snake):
        grid[r][c] = '@' if i == 0 else 'O'

    lines = []
    for row in grid:
        lines.append(''.join(_CHAR.get(ch, ch) for ch in row))

    status = (f'{CY}[{R} {WH}Score:{R} {YL}{BO}{score}{R} {CY}]{R}  '
              f'{CY}[{R} {WH}WASD/Arrows{R} {CY}]{R}  '
              f'{CY}[{R} {WH}Ctrl+Z Quit{R} {CY}]{R}')
    lines.append(status)

    sys.stdout.write('\033[H' + '\n'.join(lines))
    sys.stdout.flush()


def run_game():
    """Run one game session. Returns True to play again, False to quit."""
    snake = deque([(BOARD_HEIGHT // 2, BOARD_WIDTH // 2)])
    direction = RIGHT
    direction_queue = deque()
    food = place_food(snake)
    score = 0

    sys.stdout.write('\033[2J')

    while True:
        if read_input(direction_queue, direction):
            return False  # Ctrl+Z → skip to goodbye

        if direction_queue:
            direction = direction_queue.popleft()

        hr, hc = snake[0]
        dr, dc = direction
        new_head = (hr + dr, hc + dc)
        nr, nc = new_head

        if nr <= 0 or nr >= BOARD_HEIGHT - 1 or nc <= 0 or nc >= BOARD_WIDTH - 1:
            render(snake, food, score)
            return game_over_screen(score)

        if new_head in snake:
            render(snake, food, score)
            return game_over_screen(score)

        snake.appendleft(new_head)
        if new_head == food:
            score += 1
            food = place_food(snake)
        else:
            snake.pop()

        render(snake, food, score)
        time.sleep(TICK_SECONDS)


def main():
    enable_ansi()
    hide_cursor()
    try:
        startup_screen()
        while run_game():
            pass
        goodbye_screen()
    finally:
        show_cursor()


if __name__ == '__main__':
    main()
