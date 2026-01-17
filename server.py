import http.server, socketserver, requests, os, json, subprocess, time
from urllib.parse import urlparse, parse_qs
import os
import subprocess

PORT = 8090
MODEL = "gemini-2.5-flash-lite"

class GeminiHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query = parse_qs(parsed_url.query).get('q', [''])[0]

        if path == '/suggest':
            try:
                proc = subprocess.Popen(['./dsa_logic', query], stdout=subprocess.PIPE, text=True)
                out, _ = proc.communicate()
                suggestions = [s.strip() for s in out.split(',') if s.strip()]
                self._send_json(suggestions)
            except: self._send_json([])
            return

        elif path == '/suggest':
            try:
                # Get the absolute directory of server.py
                base_dir = os.path.dirname(os.path.abspath(__file__))
                
                # Build the correct path for the C binary
                # Linux (Render) uses 'dsa_logic', Windows uses 'dsa_logic.exe'
                binary_name = 'dsa_logic' if os.name != 'nt' else 'dsa_logic.exe'
                executable_path = os.path.join(base_dir, binary_name)

                # Call the C executable
                proc = subprocess.Popen([executable_path, query], 
                                        stdout=subprocess.PIPE, 
                                        text=True)
                out, _ = proc.communicate()
                suggestions = [s.strip() for s in out.split(',') if s.strip()]
                self._send_json(suggestions[:5])
            except Exception as e:
                print(f"Subprocess Error: {e}") # This will show in Render logs
                self._send_json([])
        
        else: return super().do_GET()

    def _send_json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

# Change this at the bottom of server.py
PORT = int(os.environ.get("PORT", 8090)) # Defaults to 8090 if not set

with socketserver.TCPServer(("", PORT), GeminiHandler) as httpd:
    httpd.allow_reuse_address = True
    print(f"Server deployed on port {PORT}")
    httpd.serve_forever()