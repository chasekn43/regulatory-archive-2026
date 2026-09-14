import http.server
import socketserver
import urllib.request
import urllib.error
import sys
import os

PORT = 8080

class ProxyRequestHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def do_GET(self):
        self.handle_proxy_request()

    def do_POST(self):
        self.handle_proxy_request()

    def handle_proxy_request(self):
        # Extract target URL from path or headers
        # For a simple reverse proxy, we map paths locally or use headers
        target_url = self.headers.get('X-Proxy-Target')
        if not target_url:
            self.send_error(400, "Missing X-Proxy-Target header indicating destination.")
            return

        print(f"[Proxy] Routing request to: {target_url}", file=sys.stderr)

        # Read POST body if present
        content_length = int(self.headers.get('Content-Length', 0))
        data = self.rfile.read(content_length) if content_length > 0 else None

        # Build request
        req = urllib.request.Request(
            target_url,
            data=data,
            method=self.command
        )

        # Copy original request headers, excluding host
        for key, value in self.headers.items():
            if key.lower() not in ['host', 'x-proxy-target']:
                req.add_header(key, value)

        # Forward request and write back response
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                self.send_response(response.status)
                
                # Copy response headers
                for key, value in response.headers.items():
                    self.send_header(key, value)
                self.end_headers()
                
                # Copy response body
                self.wfile.write(response.read())
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            for key, value in e.headers.items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as e:
            self.send_error(502, f"Bad Gateway: {str(e)}")

def run_proxy():
    # Allow address reuse
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), ProxyRequestHandler) as httpd:
        print(f"Python Local Reverse Proxy running on port {PORT}...")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down proxy server.")
            sys.exit(0)

if __name__ == "__main__":
    run_proxy()
