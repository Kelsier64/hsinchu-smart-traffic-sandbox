"""Serve only demo and public baseline files on loopback, using stdlib."""
import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {'/', '/demo/', '/demo/index.html', '/demo/app.js', '/demo/style.css',
           '/data/baseline/predictions-15min.csv', '/data/baseline/predictions-30min.csv',
           '/data/baseline/selected-observations.csv', '/data/baseline/audit.json'}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        if urlsplit(self.path).path not in ALLOWED:
            self.send_error(404)
            return
        if urlsplit(self.path).path in ['/', '/demo/']:
            self.path = '/demo/index.html'
        super().do_GET()

    def do_HEAD(self):
        if urlsplit(self.path).path not in ALLOWED:
            self.send_error(404)
            return
        super().do_HEAD()


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--port', type=int, default=8765)
    args = p.parse_args()
    print(f'Offline replay: http://127.0.0.1:{args.port}/demo/', flush=True)
    ThreadingHTTPServer(('127.0.0.1', args.port), Handler).serve_forever()
