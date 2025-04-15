import http.server
import socketserver
import os
from api.get_transcript import handler

# Set port
PORT = 8000

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

print(f"Starting server on port {PORT}...")
print(f"WebShare credentials loaded: Username={os.getenv('WEBSHARE_USERNAME')}")
print(f"Test URL: http://localhost:{PORT}/api/get_transcript?video_id=8vXoI7lUroQ")

# Create the HTTP server
with socketserver.TCPServer(("", PORT), handler) as httpd:
    print(f"Server running at http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped by user") 