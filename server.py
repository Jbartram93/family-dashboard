"""
server.py — OPTIONAL tiny web server.

Instead of generating dashboard.html and re-running after every data.py
edit, this builds the page fresh in your browser on every refresh.

  python server.py
  -> open http://localhost:8000

It uses Python's built-in http.server module — no packages to install.
"""

from http.server import BaseHTTPRequestHandler, HTTPServer

import dashboard  # importing this gives us build_page() — the same
                  # function that writes dashboard.html, just called
                  # directly instead of saved to a file.


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Runs every time the browser asks for the page."""
        html = dashboard.build_page()          # fresh build, current data
        self.send_response(200)                # 'OK'
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8")) # send the bytes

    def log_message(self, *args):
        pass  # stay quiet in the terminal (default logs every refresh)


if __name__ == "__main__":
    port = 8000
    print(f"Dashboard running -> http://localhost:{port}  (Ctrl+C to stop)")
    HTTPServer(("", port), Handler).serve_forever()
