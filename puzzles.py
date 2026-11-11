"""Generate distinct, uniquely-solvable Sudoku puzzles without external datasets."""

import random
from solver import count_solutions

CLUES = {"easy": 42, "medium": 34, "hard": 28}


def shuffled_solution(rng: random.Random) -> list[list[int]]:
    """Shuffle a canonical solved grid, preserving every Sudoku constraint."""
    digits = rng.sample(range(1, 10), 9)
    bands = rng.sample(range(3), 3)
    stacks = rng.sample(range(3), 3)
    rows = [band * 3 + i for band in bands for i in rng.sample(range(3), 3)]
    cols = [stack * 3 + i for stack in stacks for i in rng.sample(range(3), 3)]
    return [[digits[(r * 3 + r // 3 + c) % 9] for c in cols] for r in rows]


def generate_puzzle(difficulty: str = "medium", seed: int | None = None) -> dict:
    if difficulty not in CLUES:
        raise ValueError("Difficulty must be easy, medium, or hard.")
    rng = random.Random(seed)
    target = CLUES[difficulty]
    best = None

    # Retry with different randomized solutions when uniqueness prevents removal.
    for _ in range(3 if difficulty == "hard" else 2):
        solved = shuffled_solution(rng)
        puzzle = [row[:] for row in solved]
        order = rng.sample(range(81), 81)
        clues = 81

        for idx in order:
            if clues <= target:
                break
            r, c = divmod(idx, 9)
            old = puzzle[r][c]
            puzzle[r][c] = 0
            if count_solutions(puzzle) == 1:
                clues -= 1
            else:
                puzzle[r][c] = old

        if best is None or clues < best[0]:
            best = (clues, puzzle, solved)
        if clues <= target:
            break

    clues, puzzle, _solved = best
    return {"puzzle": puzzle, "difficulty": difficulty, "clues": clues}
