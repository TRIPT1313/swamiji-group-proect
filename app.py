"""Zero-dependency API and static web server for the Sudoku AI Search Lab.

Run: python app.py
Open: http://127.0.0.1:8000
"""

import argparse
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from puzzles import generate_puzzle
from solver import SudokuError, SudokuSolver, validate_board

ROOT = Path(__file__).resolve().parent / "static"
MAX_BODY_BYTES = 20_000


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def _json(self, code: int, payload: dict) -> None:
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(raw)

    def _body(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("Invalid Content-Length header.") from exc
        if not 0 < length <= MAX_BODY_BYTES:
            raise ValueError("Expected a JSON body no larger than 20 KB.")
        try:
            content = json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError("Request body must be valid JSON.") from exc
        if not isinstance(content, dict):
            raise ValueError("Expected a JSON object.")
        return content

    def do_GET(self):
        path = urlsplit(self.path)
        if path.path == "/api/puzzle":
            difficulty = parse_qs(path.query).get("difficulty", ["medium"])[0]
            if difficulty not in ("easy", "medium", "hard"):
                self._json(400, {"error": "Choose easy, medium, or hard."})
                return
            self._json(200, generate_puzzle(difficulty))
            return
        if path.path.startswith("/api/"):
            self._json(404, {"error": "Unknown endpoint."})
            return
        super().do_GET()

    def do_POST(self):
        path = urlsplit(self.path).path
        if path not in ("/api/solve", "/api/hint", "/api/check"):
            self._json(404, {"error": "Unknown endpoint."})
            return
        try:
            data = self._body()
            board = validate_board(data.get("board"))
            if path == "/api/solve":
                trace = data.get("trace", False)
                if type(trace) is not bool:
                    raise ValueError("trace must be true or false.")
                solver = SudokuSolver(board, trace=trace)
                result = solver.solve()
                if not result["solved"]:
                    self._json(422, {"error": "This board has no solution. Try undoing a move."})
                    return
                self._json(200, result)
                return
            if path == "/api/check":
                if all(v for row in board for v in row):
                    self._json(200, {"valid": True, "complete": True, "message": "Congratulations! Every row, column, and box is valid."})
                    return
                result = SudokuSolver(board).solve()
                if result["solved"]:
                    self._json(200, {"valid": True, "complete": False, "message": "No rule violations. Your current board can be completed!"})
                else:
                    self._json(200, {"valid": False, "complete": False, "message": "This arrangement cannot be solved. Revisit your entries."})
                return
            # Hint: prefer a selected empty cell, otherwise use MRV.
            result = SudokuSolver(board).solve()
            if not result["solved"]:
                self._json(422, {"error": "No solution is possible from the current board."})
                return
            selected = data.get("selected")
            if (isinstance(selected, list) and len(selected) == 2
                    and all(type(v) is int and 0 <= v < 9 for v in selected)
                    and board[selected[0]][selected[1]] == 0):
                r, c = selected
            else:
                choice = SudokuSolver(board)._pick_cell()
                if choice is None:
                    self._json(200, {"complete": True, "message": "The puzzle is already complete!"})
                    return
                r, c, _ = choice
            self._json(200, {"complete": False, "row": r, "col": c, "value": result["solution"][r][c]})
        except (SudokuError, ValueError) as exc:
            self._json(400, {"error": str(exc)})


def main():
    parser = argparse.ArgumentParser(description="Sudoku AI Search Lab")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    with ThreadingHTTPServer(("127.0.0.1", args.port), Handler) as server:
        print(f"Sudoku AI Search Lab running at http://127.0.0.1:{args.port}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nGoodbye!")


if __name__ == "__main__":
    main()
