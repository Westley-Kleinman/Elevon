#!/usr/bin/env python3
"""
Simple HTTP server for testing the frontend
"""

import http.server
import socketserver
import os

# Change to the Website directory
os.chdir('Website')

PORT = 8081

Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"🌐 Serving frontend at http://localhost:{PORT}")
    print(f"🔗 Open http://localhost:{PORT} in your browser")
    print("Press Ctrl+C to stop")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
