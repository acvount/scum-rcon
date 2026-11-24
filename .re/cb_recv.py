import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n).decode("utf-8", "replace")
        print("[RECV]", body, flush=True)
        try:
            with open(r"C:\Users\Administrator\Desktop\逆向scumserver\.re\cb_events.log", "a", encoding="utf-8") as f:
                f.write(body + "\n")
        except Exception as e:
            print("write fail", e, flush=True)
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", "2")
        self.end_headers()
        self.wfile.write(b"ok")
    def log_message(self, *a): pass
srv = ThreadingHTTPServer(("127.0.0.1", 8080), H)
srv.daemon_threads = True
print("==== LISTENING 127.0.0.1:8080 ====", flush=True)
srv.serve_forever()
