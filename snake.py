"""Snake game for Windows CMD terminal."""

import ctypes
import msvcrt
import random
import sys
import time
from collections import deque

BOARD_WIDTH = 40
BOARD_HEIGHT = 20
TICK_SECONDS = 0.1
MAX_QUEUED_TURNS = 3  # buffer rapid keypresses without losing them

# Direction constants (dr, dc)
UP    = (-1,  0)
DOWN  = ( 1,  0)
LEFT  = ( 0, -1)
RIGHT = ( 0,  1)

ARROW_MAP = {'\x48': UP, '\x50': DOWN, '\x4b': LEFT, '\x4d': RIGHT}
WASD_MAP  = {'w': UP, 's': DOWN, 'a': LEFT, 'd': RIGHT}


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
        if ch == '\x1a':  # Ctrl+Z
            quit_requested = True
            break
        new_dir = None
        if ch in ('\x00', '\xe0'):  # arrow key prefix
            ch2 = msvcrt.getwch()
            new_dir = ARROW_MAP.get(ch2)
        elif ch.lower() in WASD_MAP:
            new_dir = WASD_MAP[ch.lower()]
        if new_dir is not None and len(direction_queue) < MAX_QUEUED_TURNS:
            # Validate against last queued direction to avoid queuing a reversal
            ref = direction_queue[-1] if direction_queue else current_direction
            if not opposite(new_dir, ref) and new_dir != ref:
                direction_queue.append(new_dir)
    return quit_requested


def drain_input():
    while msvcrt.kbhit():
        msvcrt.getwch()


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
    lines = [''.join(row) for row in grid]
    lines.append(f'Score: {score}  |  WASD/Arrows to move  |  Ctrl+Z to quit')
    sys.stdout.write('\033[H' + '\n'.join(lines))
    sys.stdout.flush()


def show_centered(lines):
    top = max(0, (BOARD_HEIGHT - len(lines)) // 2)
    sys.stdout.write('\033[2J\033[H' + '\n' * top + '\n'.join(lines) + '\n')
    sys.stdout.flush()


def game_over_screen(score):
    """Show score summary screen. Returns True to restart, False to quit."""
    s = str(score)
    lines = [
        '  +------------------------------------+',
        '  |                                    |',
        '  |        * *  GAME  OVER  * *        |',
        '  |                                    |',
        f'  |         Final Score: {s:<5}         |',
        '  |                                    |',
        '  |   [R] Play Again     [Q] Quit      |',
        '  |                                    |',
        '  +------------------------------------+',
    ]
    show_centered(lines)
    drain_input()
    while True:
        ch = msvcrt.getwch().lower()
        if ch == 'r':
            return True
        if ch in ('q', '\x1a'):
            return False


GOODBYE_LINES = [
    '  +--------------------------------------+',
    '  |                                      |',
    '  |    >O>O>O>O>O>O>O>O>O>O>O>O>O>O>    |',
    '  |                                      |',
    '  |      Thanks for playing Snake!       |',
    '  |                                      |',
    '  |          See you next time!          |',
    '  |                                      |',
    '  |    <O<O<O<O<O<O<O<O<O<O<O<O<O<O<    |',
    '  |                                      |',
    '  +--------------------------------------+',
]


def goodbye_screen():
    show_centered(GOODBYE_LINES)
    time.sleep(2.5)


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
        while run_game():
            pass
        goodbye_screen()
    finally:
        show_cursor()


if __name__ == '__main__':
    main()
