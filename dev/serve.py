"""Yerel test sunucusu: kor-harita.html'i Artifact iskeletine sarıp http://localhost:8765 adresinde sunar.

Dosya her istekte yeniden okunur, değişiklikleri görmek için sayfayı yenilemek yeterli.
Kullanım: python3 dev/serve.py
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

GAME = Path(__file__).resolve().parent.parent / "kor-harita.html"
PORT = 8765

HEAD = (
    '<!doctype html><html><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
    "</head><body>"
)
TAIL = "</body></html>"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.split("?")[0] not in ("/", "/index.html"):
            self.send_error(404)
            return
        body = (HEAD + GAME.read_text(encoding="utf-8") + TAIL).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print(f"Gessit: http://localhost:{PORT}")
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
