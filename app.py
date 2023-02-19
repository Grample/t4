import json
import logging
import socket
import mimetypes
import pathlib
import urllib.parse
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from jinja2 import Environment, FileSystemLoader

StartDir=pathlib.Path()
Env=Environment(loader=FileSystemLoader('pages'))
Ip='127.0.0.1'
Buffer='1024'
Port='5000'

class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case "/":
                self.render_template('index.html')
            case "/message" | "/message.html":
                self.render_template('message.html')
            case _:
                file = StartDir / route.path[1:]
                if file.exists():
                    self.send_static(file)
                else:
                    self.render_template('error.html', 404)
    
    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))

        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self, filename):
        self.send_response(200)
        mime_type, *rest = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header('Content-Type', mime_type)
        else:
            self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        with open(filename, 'rb') as f:
            self.wfile.write(f.read())

    def render_template(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        template = Env.get_template(filename)
        html = template.render()
        self.wfile.write(html.encode())



def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ('', 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()

def save_data(data):
    body = urllib.parse.unquote_plus(data.decode())
    try:
        payload ={}
        KeyPres = str(datetime.now())
        payload[KeyPres]={key: value for key, value in [el.split('=') for el in body.split('&')]}
        with open(StartDir.joinpath('storage/data.json'), 'r') as fd:
            if fd.seek(0,2) != 0:
                fd.seek(0)
                unpacked = json.load(fd)
                payload.update(unpacked)
        with open(StartDir.joinpath('storage/data.json'), 'w', encoding='utf-8') as fd:
            json.dump(payload, fd, ensure_ascii=False, indent=4)
    except ValueError as err:
        logging.error(f"Field parse data {body} with error {err}")
    except OSError as err:
        logging.error(f"Field write data {body} with error {err}")

def run_server(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    sock.bind(server)
    try:
        while True:
            data, address = sock.recvfrom(Buffer)
            save_data(data)
    except KeyboardInterrupt:
        print(f'Destroy server')
    finally:
        sock.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(threadName)s %(message)s")
    STORAGE_DIR = pathlib.Path().joinpath('data')
    FILE_STORAGE = STORAGE_DIR / 'data.json'
    if not FILE_STORAGE.exists():
        with open(FILE_STORAGE, 'w', encoding='utf-8') as fd:
            json.dump({}, fd, ensure_ascii=False)

    thread_server = Thread(target=run)
    thread_server.start()
    thread_socket = Thread(target=run_server(Ip, Port))
    thread_socket.start()

