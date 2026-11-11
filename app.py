"""Run this file, then open http://127.0.0.1:8000 in your browser."""

import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from solver import solve_sudoku

STATIC = Path(__file__).parent / "static"


class SudokuHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC), **kwargs)

    def send_json(self, status, data):
        response = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def do_POST(self):
        if self.path != "/solve":
            self.send_json(404, {"error": "Page not found."})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 10000:
                raise ValueError("Invalid request size.")
            data = json.loads(self.rfile.read(length))
            result = solve_sudoku(data["board"])

            if result is None:
                self.send_json(422, {"error": "This Sudoku has no solution."})
            else:
                self.send_json(200, {"solution": result})
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            self.send_json(400, {"error": str(error)})


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8000), SudokuHandler)
    print("Sudoku Solver: http://127.0.0.1:8000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()
