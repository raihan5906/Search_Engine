import http.server, socketserver, requests, os, json, subprocess, time
from urllib.parse import urlparse, parse_qs

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

        elif path == '/search':
            # LEARNING STEP: Tell C to remember this search
            subprocess.Popen(['./dsa_logic', '--learn', query])
            
            api_key = os.environ.get('GEMINI_API_KEY')
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={api_key}"
            payload = {"contents": [{"parts": [{"text": query}]}]}
            
            try:
                response = requests.post(url, json=payload)
                answer = response.json()['candidates'][0]['content']['parts'][0]['text']
            except: answer = "API Error or Quota Reached."
            
            self._send_json({"query": query, "answer": answer})
            return
        
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