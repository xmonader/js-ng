import sys
from io import BytesIO
import traceback
import json
from functools import partial
import gevent
from gevent import time
from gevent.pool import Pool
from gevent.server import StreamServer
from signal import SIGTERM, SIGTERM, SIGKILL
from redis.connection import DefaultParser, Encoder
from redis.exceptions import ConnectionError
from jumpscale.god import j
from .systemactor import SystemActor
from jumpscale.core.base import Base, fields


class RedisConnectionAdapter:
    def __init__(self, sock):
        self.socket = sock
        self._sock = sock
        self.socket_timeout = 600
        self.socket_connect_timeout = 600
        self.socket_keepalive = True
        self.socket_keepalive_options = {}
        self.retry_on_timeout = True
        self.encoder = Encoder("utf", "strict", False)


class ResponseEncoder:
    def __init__(self, socket):
        self.socket = socket
        self.buffer = BytesIO()

    def encode(self, value):
        """Respond with data."""
        if value is None:
            self._write_buffer("$-1\r\n")
        elif isinstance(value, int):
            self._write_buffer(":{}\r\n".format(value))
        elif isinstance(value, bool):
            self._write_buffer(":{}\r\n".format(1 if value else 0))
        elif isinstance(value, str):
            if "\n" in value:
                self._bulk(value)
            else:
                self._write_buffer("+{}\r\n".format(value))
        elif isinstance(value, bytes):
            self._bulkbytes(value)
        elif isinstance(value, list):
            if value and value[0] == "*REDIS*":
                value = value[1:]
            self._array(value)
        elif hasattr(value, "__repr__"):
            self._bulk(value.__repr__())
        else:
            value = j.data.serializers.json.dumps(value, encoding="utf-8")
            self.encode(value)

        self._send()

    def status(self, msg="OK"):
        """Send a status."""
        self._write_buffer("+{}\r\n".format(msg))
        self._send()

    def error(self, msg):
        """Send an error."""
        # print("###:%s" % msg)
        self._write_buffer("-ERR {}\r\n".format(msg))
        self._send()

    def _bulk(self, value):
        """Send part of a multiline reply."""
        data = ["$", str(len(value)), "\r\n", value, "\r\n"]
        self._write_buffer("".join(data))

    def _array(self, value):
        """send an array."""
        self._write_buffer("*{}\r\n".format(len(value)))
        for item in value:
            self.encode(item)

    def _bulkbytes(self, value):
        data = [b"$", str(len(value)).encode(), b"\r\n", value, b"\r\n"]
        self._write_buffer(b"".join(data))

    def _write_buffer(self, data):
        if isinstance(data, str):
            data = data.encode()

        self.buffer.write(data)

    def _send(self):
        self.socket.sendall(self.buffer.getvalue())
        self.buffer = BytesIO()  # seems faster then truncating


class GedisServer(Base):
    host = fields.String(default="127.0.0.1")
    port = fields.Integer(default=16000)
    _actors = fields.Typed(dict, default={})

    def __init__(self):
        super().__init__()
        self._actors["system"] = SystemActor(self)
        self._server = StreamServer((self.host, self.port), self._on_connection)
        self._server.reuse_addr = True

    @property
    def actors(self):
        return list(self._actors.keys())

    def actor_add(self, name, path):
        if name == "system":
            raise j.exceptions.Value("invalid")

        self._actors[name] = path

    def actor_delete(self, name):
        if name == "system":
            raise j.exceptions.Value("invalid")

        if isinstance(name, bytes):
            name = name.decode()
        del self._actors[name]

    def start(self):
        for signal_type in (SIGTERM, SIGTERM, SIGKILL):
            gevent.signal(signal_type, self.stop)

        self._server.serve_forever()

    def stop(self):
        j.logger.info("Shutting down ...")
        self._server.stop()

    def _on_connection(self, socket, address):
        """Handling new connection

        Arguments:
            socket {socket} -- TCP socket
            address {tuple[str, port]} -- connection address
        """

        j.logger.info("New connection from {}", address)

        parser = DefaultParser(65536)
        conn = RedisConnectionAdapter(socket)
        encoder = ResponseEncoder(socket)
        parser.on_connect(conn)

        while True:
            try:
                response = parser.read_response()
                output = dict(success=True, error=None, result=None)

                if len(response) > 1:
                    actor_name = response[0].decode()
                    method_name = response[1].decode()
                    args = response[2:]

                    if actor_name not in self.actors:
                        output["success"] = False
                        output["error"] = "Actor not loaded"
                    else:

                        j.logger.info("Executing method {} from actor {} to client {}", method_name, actor_name, address)
                        
                        actor = self._actors[actor_name]
                        method = getattr(actor, method_name)
                        try:
                            result = method(*args)
                            
                            if isinstance(result, bytes):
                                result = result.decode()

                            output["result"] = result

                        except Exception as err:
                            output["success"] = False
                            output["error"] = str(err)

            except ConnectionError:
                j.logger.info("Client {} closed the connection", address)
                    
            except Exception as err:
                output["success"] = False
                output["error"] = "internal error: %s" % str(err)
                j.logger.error(str(err))
            
            encoder.encode(json.dumps(output))
        parser.on_disconnect()
