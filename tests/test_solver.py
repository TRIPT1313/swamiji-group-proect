import json
import sys
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import Handler
from puzzles import generate_puzzle, shuffled_solution
from solver import SudokuError, SudokuSolver, count_solutions, solve_board, validate_board


SAMPLE = [
    [0,0,0,2,6,0,7,0,1],
    [6,8,0,0,7,0,0,9,0],
    [1,9,0,0,0,4,5,0,0],
    [8,2,0,1,0,0,0,4,0],
    [0,0,4,6,0,2,9,0,0],
    [0,5,0,0,0,3,0,2,8],
    [0,0,9,3,0,0,0,7,4],
    [0,4,0,0,5,0,0,3,6],
    [7,0,3,0,1,8,0,0,0],
]


class SolverTests(unittest.TestCase):
    def test_solves_known_board_without_mutation(self):
        original = [row[:] for row in SAMPLE]
        result = solve_board(SAMPLE, trace=True)
        self.assertTrue(result['solved'])
        self.assertEqual(original, SAMPLE)
        solved = validate_board(result['solution'])
        self.assertTrue(all(v > 0 for row in solved for v in row))
        self.assertGreater(len(result['trace']), 0)
        self.assertGreater(result['stats']['nodes'], 0)
        playback = [row[:] for row in original]
        for event in result['trace']:
            playback[event['row']][event['col']] = event['value'] if event['type'] == 'place' else 0
        self.assertEqual(playback, solved)

    def test_duplicate_in_row_column_or_box(self):
        for position, digit in [((0,1), 6), ((1,0), 8), ((1,1), 6)]:
            board = [row[:] for row in SAMPLE]
            board[position[0]][position[1]] = digit
            with self.assertRaises(SudokuError):
                validate_board(board)

    def test_bad_shapes_types_and_bool(self):
        for board in [None, [], [[0]*9]*8, [[0]*9]*8 + [[0]*8], [[0]*9]*8 + [[True]*9]]:
            with self.assertRaises(SudokuError):
                validate_board(board)

    def test_unsolvable_but_no_duplicate(self):
        bad = [row[:] for row in SAMPLE]
        bad[0][0] = 3
        validate_board(bad)
        self.assertFalse(solve_board(bad)['solved'])

    def test_empty_board_has_multiple_solutions(self):
        self.assertEqual(count_solutions([[0]*9 for _ in range(9)]), 2)

    def test_solved_board_returns_no_trace(self):
        solution = solve_board(SAMPLE)['solution']
        res = solve_board(solution, trace=True)
        self.assertEqual(res['solution'], solution)
        self.assertEqual(res['trace'], [])
        self.assertEqual(res['stats']['placements'], 0)

    def test_trace_limit(self):
        res = SudokuSolver(SAMPLE, trace=True, trace_limit=2).solve()
        self.assertEqual(len(res['trace']), 2)
        self.assertTrue(res['stats']['trace_capped'])

    def test_generated_puzzles_are_unique(self):
        for difficulty, target in [('easy',42),('medium',34),('hard',28)]:
            with self.subTest(difficulty=difficulty):
                generated = generate_puzzle(difficulty, seed=17)
                board = generated['puzzle']
                self.assertLessEqual(generated['clues'], 50)
                self.assertGreaterEqual(generated['clues'], target)
                self.assertEqual(count_solutions(board), 1)
                solution = solve_board(board)['solution']
                self.assertEqual(validate_board(solution), solution)

    def test_randomized_full_grid_valid(self):
        import random
        board = shuffled_solution(random.Random(42))
        self.assertEqual(validate_board(board), board)
        self.assertTrue(all(v > 0 for row in board for v in row))


class APITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.url = 'http://127.0.0.1:' + str(cls.server.server_address[1])
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def call(self, path, body=None):
        data = json.dumps(body).encode('utf-8') if body is not None else None
        req = Request(self.url + path, data=data, headers={'Content-Type':'application/json'})
        try:
            with urlopen(req, timeout=10) as response:
                return response.status, json.load(response)
        except HTTPError as exc:
            return exc.code, json.load(exc)

    def test_serves_frontend(self):
        with urlopen(self.url + '/', timeout=10) as response:
            text = response.read().decode('utf-8')
        self.assertIn('Sudoku board', text)

    def test_puzzle_endpoint(self):
        status, body = self.call('/api/puzzle?difficulty=easy')
        self.assertEqual(status, 200)
        self.assertEqual(body['difficulty'], 'easy')
        self.assertEqual(count_solutions(body['puzzle']), 1)

    def test_solve_check_hint(self):
        status, body = self.call('/api/solve', {'board':SAMPLE, 'trace':True})
        self.assertEqual(status, 200)
        self.assertTrue(body['solved'])
        status, check = self.call('/api/check', {'board':SAMPLE})
        self.assertEqual(status, 200)
        self.assertTrue(check['valid'])
        self.assertFalse(check['complete'])
        status, hint = self.call('/api/hint', {'board':SAMPLE, 'selected':[0,0]})
        self.assertEqual(status, 200)
        self.assertEqual((hint['row'], hint['col']), (0,0))
        self.assertEqual(hint['value'], body['solution'][0][0])

    def test_bad_input(self):
        status, body = self.call('/api/solve', {'board':[[1]*9 for _ in range(9)]})
        self.assertEqual(status, 400)
        self.assertIn('error',body)
        status, body = self.call('/api/puzzle?difficulty=impossible')
        self.assertEqual(status, 400)
        status, body = self.call('/api/solve', {'board':SAMPLE, 'trace':'true'})
        self.assertEqual(status, 400)


if __name__ == '__main__':
    unittest.main()
