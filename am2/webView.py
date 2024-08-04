from typing import override
import flet as ft
import sql
import AES
from decimal import Decimal
import sqlite3
import base64
import threading
import http.server
import socketserver
import webview
from accountManager2 import *

def start_server():
    Handler = http.server.SimpleHTTPRequestHandler
    PORT = 5000
    httpd = socketserver.TCPServer(("", PORT), Handler)
    httpd.serve_forever()

if __name__ == '__main__':
    # Start the local server in a separate thread
    threading.Thread(target=start_server, daemon=True).start()
    # Start the Flet app
    ft.app(target=main, view=ft.WEB_BROWSER)
    # Open the app in a webview
    width = 400
    height = width*16/9
    webview.create_window('Account Manager 2', 'http://localhost:5000', width=width, height=height)
    webview.start()
