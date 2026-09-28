"""Serves tests/mock, plus /hang which never responds - so pages that use it never finish loading."""
import http.server, socketserver, time, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
class H(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/hang"):
            time.sleep(3600); return
        super().do_GET()
    def log_message(self, *a): pass
socketserver.ThreadingTCPServer.allow_reuse_address = True
socketserver.ThreadingTCPServer(("", 8766), H).serve_forever()
