# Sudoku Solver Using Backtracking

This is a simple beginner-friendly AI project that automatically solves 9×9 Sudoku puzzles using **backtracking**, a classical AI search technique.

## Features

- Enter numbers in a Sudoku grid.
- Click **Solve Sudoku** to fill empty cells.
- Click **Clear** to empty the board.
- Click **Example** to load a sample puzzle.
- Displays a message when the puzzle is invalid or cannot be solved.

## Technologies

- Python (backtracking algorithm and simple web server)
- HTML, CSS and JavaScript (basic interface)
- No extra libraries required

## How to run

1. Install Python 3.10 or later.
2. Open this project folder in VS Code.
3. Open the terminal and run:

   ```bash
   python app.py
   ```

   On Windows, if `python` does not work, try `py app.py`.
4. Open http://127.0.0.1:8000 in your browser.

Press **Ctrl + C** in the terminal to stop the server.

## How it works

1. Empty cells are represented by `0`.
2. The program finds an empty cell.
3. It tries numbers 1–9 in the cell.
4. A number is allowed only when it does not appear in the same row, column, or 3×3 box.
5. The program moves to the next empty cell.
6. If no number works, it **backtracks** (erases the previous guess and tries another).
7. When every cell is filled, the solution is displayed.

Backtracking is a **classical AI search method**. This project does not use machine learning.

## Project files

```text
sudoku-solver-beginner/
├── app.py             # Starts the local server
├── solver.py          # Sudoku backtracking algorithm
├── static/
│   └── index.html     # Simple web page with HTML, CSS and JS
├── tests/
│   └── test_solver.py # Basic tests
├── .gitignore
└── README.md
```

## Run tests (optional)

```bash
python -m unittest discover -s tests -v
```

## Example input

A 9×9 board containing numbers from 1 to 9, with `0` for empty cells.
The **Example** button loads one automatically.

## Time complexity

In the worst case, backtracking tries multiple possibilities for each empty cell, so time complexity is exponential: up to **O(9^E)** for `E` empty cells. The recursion uses up to **O(E)** extra space.

## Notes

Run `app.py` before opening the webpage, because the browser sends the Sudoku grid to the Python solver. This project is intended for learning and local demonstrations.
