#!/usr/bin/env python3

import json
import hashlib
import logging
import os
import structlog

from tornado import autoreload
from tornado.gen import coroutine, sleep
from tornado.httpclient import HTTPRequest
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.options import options
from tornado.process import cpu_count
from tornado.web import Application as BaseApplication
from tornado.web import RequestHandler, StaticFileHandler
from tornado.websocket import WebSocketHandler, websocket_connect


app_settings = {
    "default_handler_args": dict(status_code=404),
    "env": os.environ.get("ENV", "dev"),
    "log_level": os.environ.get("LOG_LEVEL", "INFO"),
    "port": os.environ.get("APP_PORT", "8000"),
    "static_path": os.path.join(os.path.dirname(__file__), "public/assets"),
    "static_url_prefix": "/assets/",
    "template_path": os.path.join(os.path.dirname(__file__), "public"),
    "boatpi_ws": os.environ.get("BOATPI_WS", "ws://localhost:8001/ws"),
    "websocket_ping_interval": 10,
    "compression_options": {},
}

logging.basicConfig(
    level=getattr(logging, app_settings["log_level"]),
    format="[%(levelname)s %(asctime)s path:%(pathname)s lineno:%(lineno)s] %(message)s",  # noqa
    datefmt="%Y-%m-%d %I:%M:%S"
)

structlog.configure(logger_factory=structlog.stdlib.LoggerFactory())
log = structlog.get_logger()

options.logging = None  # configure Tornado to leave logging alone


admin_tokens = [
    # Tizio Qualunque
    "10df398b4321258ad07e7127080bc497d80818b77b8cc38f4e8fd2992ec7fa497154d222e844fb48743008ecfa05d9f8446012ed5d1f92cc7e10d649cdf38c50"
]


boat = None


class HomeHandler(RequestHandler):
    """Serves application home information."""

    async def get(self, *args, **kwargs):
        """A function that will return the content for the home endpoint."""
        log.info("Endpoint hit", handler="home")
        items = ["Item 1", "Item 2", "Item 3"]
        self.render("home.html", title="My title", items=items)

    def data_received(self, chunk):
        """Defined to avoid abstract-method lint issue."""
        pass


class WSHandler(WebSocketHandler):
    clients = []
    admins = []
    viewers = []

    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    def open(self):
        WSHandler.clients.append(self)
        WSHandler.viewers.append(self)
        logging.info("A new client connected, there are %d admins and %d viewers connected", len(self.admins), len(self.viewers))

    def on_close(self):
        WSHandler.clients.remove(self)
        WSHandler.admins.remove(self)
        WSHandler.viewers.remove(self)
        logging.info("A client disconnected, there are %d admins and %d viewers connected", len(self.admins), len(self.viewers))

    async def on_message(self, message):
        data = json.loads(message)
        logging.info('New message received "%s"', message)

        if data['action'] == 'authenticate':
            token = '';

            if 'token' in data:
                token = data['token']
            elif 'username' in data and 'password' in data:
                token = hashlib.sha512((data['username']+'§'+data['password']).encode('utf-8')).hexdigest()

            if token in admin_tokens:
                WSHandler.admins.append(self)
                WSHandler.viewers.remove(self)
                logging.info("Viewer authenticated successfully, there are %d admins and %d viewers now", len(self.admins), len(self.viewers))
                self.write_message(json.dumps({'event': 'authentication', 'status': 'success', 'token': token}))
            else:
                logging.info("Authentication failure")
                self.write_message(json.dumps({'event': 'authentication', 'status': 'failure'}))

    def check_origin(self, origin):
        return True

    @classmethod
    def talk_to_admins(self, message):
        logging.info('Sending a message to %d admins', len(self.admins))
        serialized = json.dumps(message)

        for client in self.admins:
            try:
                client.write_message(serialized)
            except:
                logging.error('Error sending message', exc_info=True)

    @classmethod
    def talk_to_viewers(self, message):
        logging.info('Sending a message to %d viewers', len(self.viewers))
        serialized = json.dumps(message)

        for client in self.viewers:
            try:
                client.write_message(serialized)
            except:
                logging.error('Error sending message', exc_info=True)

    @classmethod
    def talk_to_all(self, message):
        logging.info('Sending a message to %d clients', len(self.clients))
        serialized = json.dumps(message)

        for client in self.clients:
            try:
                client.write_message(serialized)
            except:
                logging.error('Error sending message', exc_info=True)

class BoatPi:
    """A class that talks with the boat on the sea."""

    def __init__(self, url, timeout):
        self.url = url
        self.timeout = timeout
        self.ioloop = IOLoop.instance()
        self.ws = None

        self.connect()

        PeriodicCallback(self.keep_alive, 5000).start()

    @coroutine
    def connect(self):
        """Setup the connection to the boat."""
        try:
            self.ws = yield websocket_connect(self.url)
        except:
            logging.info("BoatPi connection error")
            WSHandler.talk_to_all("BoatPi connection error")
        else:
            WSHandler.talk_to_all("BoatPi connected")
            self.run()

    @coroutine
    def run(self):
        while True:
            msg = yield self.ws.read_message()
            if msg is None:
                self.ws = None
                logging.info("BoatPi connection closed")
                WSHandler.talk_to_all("BoatPi connection lost")
                break

            self.on_message(msg)

    @coroutine
    def on_message(self, message):
        WSHandler.talk_to_all(message)

    def keep_alive(self):
        """Re-connect is connection got lost"""
        if self.ws is None:
            self.connect()
        #else:
        #    self.ws.write_message(json.dumps("keep alive"))


class Application(BaseApplication):
    """Base Application class to define the app's routes and settings."""

    def __init__(self):
        """Setup the routes and import the application settings."""
        app_handlers = [
            ("/", HomeHandler),
            ("/ws", WSHandler),
        ]

        super().__init__(app_handlers, **app_settings)


if __name__ == "__main__":
    boat = BoatPi(app_settings["boatpi_ws"], 5)

    if app_settings["env"] == "dev":
        log.info("Starting applications", mode="single")
        Application().listen(app_settings["port"])
        autoreload.start()
        autoreload.watch(r'public/')
    else:
        log.info("Starting applications", mode="forked", cpu_count=cpu_count())
        server = HTTPServer(Application())
        server.bind(app_settings["port"])
        server.start(0)  # multi process mode (one process per cpu)

    ioloop = IOLoop.instance()
    ioloop.start()

