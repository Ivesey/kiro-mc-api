# Project Steering: Multicloud NoSQL API

## Overview

This is a Python 3 project.

## Project Structure


## Python Environment

- Always use the project virtual environment: `venv/`
- venv is in the project root directory
- Install dependencies from `requirements.txt`: `venv\Scripts\pip install -r requirements.txt`
- Run tests using the venv pytest
- Never install packages into the global Python environment — always activate the venv or use `venv\Scripts\pip` directly.
- Pin all dependencies in `requirements.txt` with exact versions (`==`).

## Application Behaviour


## Coding Conventions

- Use the standard library whenever possible.
- Do not introduce other third-party CLI libraries unless explicitly discussed.
- Follow standard Python idioms.

## Testing

- When adding new features, add corresponding tests covering the acceptance criteria.
- Use `unittest.mock.patch` to mock dependencies for unit tests.
- Never modify a unit test without explicit approval.

## Spec Workflow

- This project follows the Kiro spec workflow: Requirements → Design → Tasks.
- Update the spec when requirements or design decisions change.
- Acceptance criteria in `tasks.md` should be kept in sync with the unit tests.
