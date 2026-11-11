"""Sudoku as a constraint-satisfaction problem (CSP).

Search uses backtracking, Minimum Remaining Values (MRV), and bitmask
constraints for row, column and 3x3 box uniqueness. No external packages.
"""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

FULL_MASK = (1 << 9) - 1


class SudokuError(ValueError):
    """Raised when an input Sudoku board is malformed or contradictory."""


def validate_board(board: object) -> list[list[int]]:
    """Return a defensive copy of a valid 9x9 board (0 denotes empty)."""
    if not isinstance(board, list) or len(board) != 9:
        raise SudokuError("The board must contain exactly 9 rows.")

    copy = []
    for r, row in enumerate(board):
        if not isinstance(row, list) or len(row) != 9:
            raise SudokuError(f"Row {r + 1} must contain exactly 9 cells.")
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            raise SudokuError("Cells must be integers between 0 and 9.")
        copy.append(row[:])

    for unit in (
        *copy,
        *([copy[r][c] for r in range(9)] for c in range(9)),
        *(
            [copy[r][c] for r in range(br, br + 3) for c in range(bc, bc + 3)]
            for br in (0, 3, 6)
            for bc in (0, 3, 6)
        ),
    ):
        nonzero = [v for v in unit if v != 0]
        if len(nonzero) != len(set(nonzero)):
            raise SudokuError("Duplicate digit found in a row, column, or 3×3 box.")
    return copy


@dataclass
class SearchStats:
    nodes: int = 0
    placements: int = 0
    backtracks: int = 0
    elapsed_ms: float = 0.0
    trace_capped: bool = False

    def as_dict(self) -> dict:
        return {
            "nodes": self.nodes,
            "placements": self.placements,
            "backtracks": self.backtracks,
            "elapsed_ms": round(self.elapsed_ms, 2),
            "trace_capped": self.trace_capped,
        }


class SudokuSolver:
    def __init__(self, board: list[list[int]], trace: bool = False, trace_limit: int = 12000):
        self.board = validate_board(board)
        self.rows = [0] * 9
        self.cols = [0] * 9
        self.boxes = [0] * 9
        self.trace_enabled = trace
        self.trace_limit = max(0, min(int(trace_limit), 50000))
        self.trace = []
        self.stats = SearchStats()
        self.solutions = []

        for r in range(9):
            for c in range(9):
                value = self.board[r][c]
                if value:
                    bit = 1 << (value - 1)
                    box = self._box(r, c)
                    self.rows[r] |= bit
                    self.cols[c] |= bit
                    self.boxes[box] |= bit

    @staticmethod
    def _box(r: int, c: int) -> int:
        return r // 3 * 3 + c // 3

    def _candidates(self, r: int, c: int) -> int:
        used = self.rows[r] | self.cols[c] | self.boxes[self._box(r, c)]
        return FULL_MASK & ~used

    def _pick_cell(self) -> tuple[int, int, int] | None:
        """MRV: choose the empty cell with the fewest legal values."""
        best = None
        min_count = 10
        for r in range(9):
            for c in range(9):
                if self.board[r][c] == 0:
                    options = self._candidates(r, c)
                    count = options.bit_count()
                    if count < min_count:
                        best = (r, c, options)
                        min_count = count
                        if count <= 1:
                            return best
        return best

    def _record(self, kind: str, r: int, c: int, value: int, depth: int) -> None:
        if not self.trace_enabled:
            return
        if len(self.trace) < self.trace_limit:
            self.trace.append({
                "type": kind,
                "row": r,
                "col": c,
                "value": value,
                "depth": depth,
            })
        else:
            self.stats.trace_capped = True

    def _place(self, r: int, c: int, value: int) -> None:
        bit = 1 << (value - 1)
        self.board[r][c] = value
        self.rows[r] |= bit
        self.cols[c] |= bit
        self.boxes[self._box(r, c)] |= bit

    def _remove(self, r: int, c: int, value: int) -> None:
        bit = ~(1 << (value - 1))
        self.board[r][c] = 0
        self.rows[r] &= bit
        self.cols[c] &= bit
        self.boxes[self._box(r, c)] &= bit

    def _search(self, limit: int, depth: int) -> bool:
        self.stats.nodes += 1
        choice = self._pick_cell()
        if choice is None:
            self.solutions.append([row[:] for row in self.board])
            return len(self.solutions) >= limit

        r, c, options = choice
        while options:
            bit = options & -options
            options ^= bit
            value = bit.bit_length()
            self._place(r, c, value)
            self.stats.placements += 1
            self._record("place", r, c, value, depth)
            if self._search(limit, depth + 1):
                return True
            self._remove(r, c, value)
            self.stats.backtracks += 1
            self._record("backtrack", r, c, value, depth)
        return False

    def solve(self, max_solutions: int = 1) -> dict:
        if max_solutions not in (1, 2):
            raise ValueError("max_solutions must be 1 or 2")
        start = perf_counter()
        self._search(max_solutions, 0)
        self.stats.elapsed_ms = (perf_counter() - start) * 1000
        return {
            "solved": bool(self.solutions),
            "solution": self.solutions[0] if self.solutions else None,
            "solution_count": len(self.solutions),
            "stats": self.stats.as_dict(),
            "trace": self.trace,
        }


def solve_board(board: list[list[int]], trace: bool = False, trace_limit: int = 12000) -> dict:
    return SudokuSolver(board, trace=trace, trace_limit=trace_limit).solve()


def count_solutions(board: list[list[int]], limit: int = 2) -> int:
    return SudokuSolver(board).solve(max_solutions=limit)["solution_count"]
