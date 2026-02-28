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

# Direction constants (dr, dc)
UP = (-1, 0)
DOWN = (1, 0)
LEFT = (0, -1)
RIGHT = (0, 1)

ARROW_MAP = {
    '\x48': UP,
    '\x50': DOWN,
    '\x4b': LEFT,
    '\x4d': RIGHT,
}

WASD_MAP = {
    'w': UP,
    's': DOWN,
    'a': LEFT,
    'd': RIGHT,
}


def enable_ansi():
    """Enable ANSI virtual terminal processing in Windows CMD."""
    ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
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
    snake_set = set(snake)
    while True:
        r = random.randint(1, BOARD_HEIGHT - 2)
        c = random.randint(1, BOARD_WIDTH - 2)
        if (r, c) not in snake_set:
            return (r, c)


def render(snake, food, score, out):
    grid = [['#' if r == 0 or r == BOARD_HEIGHT - 1 or c == 0 or c == BOARD_WIDTH - 1
              else ' '
              for c in range(BOARD_WIDTH)]
             for r in range(BOARD_HEIGHT)]

    fr, fc = food
    grid[fr][fc] = '*'

    for i, (r, c) in enumerate(snake):
        grid[r][c] = '@' if i == 0 else 'O'

    lines = [''.join(row) for row in grid]
    status = f'Score: {score}  |  WASD/Arrows to move  |  Ctrl+Z to quit'
    lines.append(status)

    out.write('\033[H' + '\n'.join(lines))
    out.flush()


def read_input():
    """Drain all pending keypresses, return the last valid direction key or quit signal."""
    direction_key = None
    quit_requested = False

    while msvcrt.kbhit():
        ch = msvcrt.getwch()
        if ch == '\x1a':  # Ctrl+Z
            quit_requested = True
            break
        if ch in ('\x00', '\xe0'):  # arrow key prefix
            ch2 = msvcrt.getwch()
            if ch2 in ARROW_MAP:
                direction_key = ARROW_MAP[ch2]
        elif ch.lower() in WASD_MAP:
            direction_key = WASD_MAP[ch.lower()]

    return direction_key, quit_requested


def opposite(d1, d2):
    return d1[0] == -d2[0] and d1[1] == -d2[1]


def game_over_screen(score):
    msg = f'GAME OVER -- Score: {score} -- Press any key to exit'
    col = (BOARD_WIDTH - len(msg)) // 2
    row = BOARD_HEIGHT // 2
    sys.stdout.write(f'\033[{row + 1};{col + 1}H{msg}')
    sys.stdout.flush()
    # Drain existing input then wait for a fresh keypress
    while msvcrt.kbhit():
        msvcrt.getwch()
    msvcrt.getwch()


def main():
    enable_ansi()
    sys.stdout.write('\033[2J')  # clear screen once at start
    hide_cursor()

    try:
        snake = deque([(BOARD_HEIGHT // 2, BOARD_WIDTH // 2)])
        direction = RIGHT
        food = place_food(snake)
        score = 0
        grow_pending = False

        out = sys.stdout

        while True:
            direction_key, quit_requested = read_input()

            if quit_requested:
                break

            if direction_key is not None and not opposite(direction_key, direction):
                direction = direction_key

            head_r, head_c = snake[0]
            dr, dc = direction
            new_head = (head_r + dr, head_c + dc)
            nr, nc = new_head

            # Wall collision
            if nr <= 0 or nr >= BOARD_HEIGHT - 1 or nc <= 0 or nc >= BOARD_WIDTH - 1:
                render(snake, food, score, out)
                game_over_screen(score)
                break

            # Self collision
            if new_head in snake:
                render(snake, food, score, out)
                game_over_screen(score)
                break

            if new_head == food:
                score += 1
                grow_pending = True
                food = place_food(deque([new_head]) if not snake else snake)

            snake.appendleft(new_head)
            if grow_pending:
                grow_pending = False
            else:
                snake.pop()

            render(snake, food, score, out)
            time.sleep(TICK_SECONDS)

    finally:
        show_cursor()


if __name__ == '__main__':
    main()
