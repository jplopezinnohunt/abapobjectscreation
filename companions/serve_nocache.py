"""Tiny static server that disables browser caching (Cache-Control: no-store).
Run from companions/:  python serve_nocache.py 8800
"""
import sys
from http.server import SimpleHTTPRequestHandler, HTTPServer


class NoCache(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


port = int(sys.argv[1]) if len(sys.argv) > 1 else 8800
HTTPServer(("127.0.0.1", port), NoCache).serve_forever()
