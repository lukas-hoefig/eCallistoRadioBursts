import http.server
import socketserver
import os 

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Expires', '0')
        http.server.SimpleHTTPRequestHandler.end_headers(self)

PORT = 8000

current_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)))

# Change the current directory to the directory you want to serve files from
os.chdir(current_dir)

with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
    print("Server started at http://localhost:{}/".format(PORT))
    httpd.serve_forever()