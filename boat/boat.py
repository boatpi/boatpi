#!/usr/bin/env python3
# ____              _   ____  _
#| __ )  ___   __ _| |_|  _ \(_)
#|  _ \ / _ \ / _` | __| |_) | |
#| |_) | (_) | (_| | |_|  __/| |
#|____/ \___/ \__,_|\__|_|   |_|

import json
import logging
import os
import psutil
import structlog
import time

from math import sin, cos, pi

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

from huawei_lte_api.Connection import Connection as ModemConnection
from huawei_lte_api.Client import Client as ModemClient

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
        return "READY TO SAIL"

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

        if 'power' in data:
            GPIOHandler.set_power(data['power'])
            self.talk_to_clients({'power': Status.power})

        if 'wheel' in data:
            GPIOHandler.set_wheel(data['wheel'])
            self.talk_to_clients({'wheel': Status.wheel})


    def check_origin(self, origin):
        return True

    @classmethod
    def talk_to_clients(self, message):
        message['timestamp'] = time.time()

        logging.info(message)
        serialized = json.dumps(message)
        logging.info('Sending ' + serialized)

        for client in self.clients:
            try:
                client.write_message(serialized)
            except:
                logging.error('Error sending message', exc_info=True)


class Status:
    """A class that stores all metadata like position, direction, power, load, signal, etc."""

    power = 0 # How many power give to the main boat's motor
    wheel = 0 # How is the boat's wheel set

    def __init__(self):
        PeriodicCallback(self.collect, 1000).start()

    @coroutine
    def collect(self):
        """Setup the connection to the boat."""

        data = dict()

        data['cpu_load'] = psutil.cpu_percent(interval=1)
        data['memory'] = Status.get_memory_data()
        data['gps_position'] = GpsTracker.get_data()
        data['modem'] = ModemHandler.status()

        WSHandler.talk_to_clients(data)

    @classmethod
    def get_memory_data(self):
        virtual = psutil.virtual_memory()
        return {
            'total': virtual.total,
            'available': virtual.available,
            'used': virtual.used,
            'free': virtual.free,
            'percent': virtual.percent,
        }


class GpsTracker:
    """Query GPS module and stores geographic position data."""

    latitude = 40.203636
    longitude = 16.728161
    speed = 0.0
    direction = 0.0

    @classmethod
    def autopilot(self):
        # Simulate that boat is moving
        # TODO: Remove this before sail
        GpsTracker.speed = Status.power/18630.547
        GpsTracker.direction = GpsTracker.direction+Status.wheel/50
        GpsTracker.latitude = GpsTracker.latitude+GpsTracker.speed*cos(GpsTracker.direction)
        GpsTracker.longitude = GpsTracker.longitude+GpsTracker.speed*sin(GpsTracker.direction)

    @classmethod
    def get_data(self):
        self.autopilot()

        return {
            'latitude': GpsTracker.latitude,
            'longitude': GpsTracker.longitude,
            'speed': GpsTracker.speed,
            'direction': GpsTracker.direction,
        }


class GPIOHandler:
    """Read/Write raw data from/to GPIO"""

    @classmethod
    def set_power(self, value):
        if value < -20 or value > 100:
            return

        # TODO: Set MOTOR power
        Status.power = value

    @classmethod
    def set_wheel(self, value):
        if value < -50 or value > 50:
            return

        # TODO: Set WHEEL position
        Status.wheel = value

    @coroutine
    def watcher(self):
        if not is_raspberry:
            return

        try:
            while True:
                pass

        finally:
            GPIO.cleanup()


class ModemHandler:
    """Handle LTE Modem"""

    @classmethod
    def status(self):
        try:
            connection = ModemConnection('http://192.168.8.1/')
            client = ModemClient(connection)

            return client.device.signal()
        except:
            pass


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
    else:
        log.info("Starting applications", mode="forked", cpu_count=cpu_count())
        server = HTTPServer(Application())
        server.bind(app_settings["port"])
        server.start(0)  # multi process mode (one process per cpu)

    IOLoop.current().start()
