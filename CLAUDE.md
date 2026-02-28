# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

HelloClaude is a toy project for learning and experimenting with Claude Code. It is in early stages with no source code yet.

## Language

The `.gitignore` is configured for Python (including support for pip, uv, poetry, pdm, pixi, pytest, mypy, ruff, and common Python IDEs). New code added to this project should follow Python conventions unless the user indicates otherwise.

## Commands
- Run the snake game: `python snake.py`

## Backlog Workflow
- Track bugs and features in `BACKLOG.md`
- When an item is completed, remove it from its section in `BACKLOG.md` and append it to `ARCHIVED.md` under the appropriate heading (`## Features` or `## Bugs`)
- Keep `BACKLOG.md` clean — it should only contain pending work

## Git Workflow
- Each new feature gets its own branch: `git checkout -b feature/<name>`
- Commit work incrementally on the feature branch
- Once the feature is fully complete, merge back to main: `git checkout main && git merge feature/<name>`
- Delete the feature branch after merging: `git branch -d feature/<name>`
