"""Simple Sudoku solver using backtracking."""


def is_valid(board, row, col, number):
    # Check the row and column.
    for i in range(9):
        if board[row][i] == number or board[i][col] == number:
            return False

    # Check the 3 x 3 box.
    start_row = (row // 3) * 3
    start_col = (col // 3) * 3
    for r in range(start_row, start_row + 3):
        for c in range(start_col, start_col + 3):
            if board[r][c] == number:
                return False
    return True


def solve(board):
    # Find the first empty cell (represented by 0).
    for row in range(9):
        for col in range(9):
            if board[row][col] == 0:
                for number in range(1, 10):
                    if is_valid(board, row, col, number):
                        board[row][col] = number

                        if solve(board):
                            return True

                        # The choice failed, so try another number.
                        board[row][col] = 0
                return False
    return True


def solve_sudoku(board):
    # Validate input before solving.
    if not isinstance(board, list) or len(board) != 9:
        raise ValueError("The Sudoku board must have 9 rows.")
    for row in board:
        if not isinstance(row, list) or len(row) != 9:
            raise ValueError("Each row must contain 9 numbers.")
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            raise ValueError("Use numbers from 1 to 9, or 0 for empty cells.")

    grid = [row[:] for row in board]
    for row in range(9):
        for col in range(9):
            number = grid[row][col]
            if number != 0:
                grid[row][col] = 0
                if not is_valid(grid, row, col, number):
                    raise ValueError("Invalid Sudoku: a number is repeated.")
                grid[row][col] = number

    if solve(grid):
        return grid
    return None
