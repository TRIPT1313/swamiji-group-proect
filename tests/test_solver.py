import unittest
from solver import is_valid, solve_sudoku


SAMPLE = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9],
]


class SudokuTests(unittest.TestCase):
    def test_solve_example(self):
        solved = solve_sudoku(SAMPLE)
        self.assertEqual(solved[0], [5, 3, 4, 6, 7, 8, 9, 1, 2])
        self.assertEqual(solved[8], [3, 4, 5, 2, 8, 6, 1, 7, 9])
        self.assertTrue(all(0 not in row for row in solved))

    def test_does_not_change_input(self):
        original = [row[:] for row in SAMPLE]
        solve_sudoku(SAMPLE)
        self.assertEqual(SAMPLE, original)

    def test_invalid_row(self):
        board = [row[:] for row in SAMPLE]
        board[0][2] = 5
        with self.assertRaises(ValueError):
            solve_sudoku(board)

    def test_invalid_column(self):
        board = [row[:] for row in SAMPLE]
        board[1][1] = 3
        with self.assertRaises(ValueError):
            solve_sudoku(board)

    def test_invalid_box(self):
        board = [row[:] for row in SAMPLE]
        board[1][1] = 9
        with self.assertRaises(ValueError):
            solve_sudoku(board)

    def test_invalid_shape(self):
        with self.assertRaises(ValueError):
            solve_sudoku([[1, 2, 3]])

    def test_invalid_cell(self):
        board = [row[:] for row in SAMPLE]
        board[0][2] = 10
        with self.assertRaises(ValueError):
            solve_sudoku(board)

    def test_valid_choice(self):
        self.assertTrue(is_valid(SAMPLE, 0, 2, 4))
        self.assertFalse(is_valid(SAMPLE, 0, 2, 5))


if __name__ == "__main__":
    unittest.main()
