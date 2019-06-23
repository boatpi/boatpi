#!/usr/bin/env python3

import json
import hashlib
import logging
import os
import structlog

from tornado import autoreload
from tornado.gen import coroutine, sleep
from tornado.httpclient import AsyncHTTPClient
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.options import options
from tornado.process import cpu_count
from tornado.web import Application as BaseApplication
from tornado.web import RequestHandler, StaticFileHandler
from tornado.websocket import WebSocketHandler

BUTTON_PIN = 17 # BCM
BUTTON_PIN = 11 # BOARD
RELAY_PINS = [19, 16, 26, 20, 13, 6, 5, 12] # BCM
RELAY_PINS = [35, 36, 37, 38, 33, 31, 29, 32] # BOARD
DOOR_RELAY = 4
GATE_RELAY = 2

is_raspberry = os.path.exists('/dev/gpiomem')

if is_raspberry:
    import RPi.GPIO as GPIO

    # GPIO.setmode(GPIO.BCM)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down = GPIO.PUD_UP)
    GPIO.setup(RELAY_PINS, GPIO.OUT, initial = GPIO.HIGH)


app_settings = {
    "default_handler_args": dict(status_code=404),
    "env": os.environ.get("ENV", "dev"),
    "log_level": os.environ.get("LOG_LEVEL", "INFO"),
    "port": os.environ.get("APP_PORT", "8001"),
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


status = None


class HomeHandler(RequestHandler):
    """Serves application home information."""

    async def get(self, *args, **kwargs):
        return "READY"

    def data_received(self, chunk):
        """Defined to avoid abstract-method lint issue."""
        pass


class WSHandler(WebSocketHandler):
    clients = []

    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    def open(self):
        WSHandler.clients.append(self)
        logging.info("A new client connected, there are %d clients connected", len(self.clients))

    def on_close(self):
        WSHandler.clients.remove(self)
        logging.info("A client disconnected, there are %d clients connected", len(self.clients))

    def on_message(self, message):
        logging.info('Received ' + message)
        data = json.loads(message)

        self.talk_to_clients(data)

    def check_origin(self, origin):
        return True

    @classmethod
    def talk_to_clients(self, message):
        serialized = json.dumps(message)
        logging.info('Sending ' + serialized)

        for client in self.clients:
            try:
                client.write_message(serialized)
            except:
                logging.error('Error sending message', exc_info=True)


class Status(object):
    """A class that talks with the boat on the sea."""

    def __init__(self):
        self.counter = 0

        PeriodicCallback(self.collect, 1000).start()

    @coroutine
    def collect(self):
        """Setup the connection to the boat."""
        self.counter = self.counter + 1
        WSHandler.talk_to_clients(self.__dict__)


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
    status = Status()

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

    IOLoop.current().start()
