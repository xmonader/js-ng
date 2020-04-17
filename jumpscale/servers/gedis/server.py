import sys
from io import BytesIO
import better_exceptions
import json
from functools import partial
import gevent
import inspect
from gevent import time
from gevent.pool import Pool
from gevent.server import StreamServer
from signal import SIGTERM, SIGTERM, SIGKILL
from redis.connection import DefaultParser, Encoder
from .baseactor import BaseActor
from redis.exceptions import ConnectionError
from jumpscale.god import j
from .systemactor import CoreActor, SystemActor
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


RESERVED_ACTOR_NAMES = ("core", "system")


class GedisServer(Base):
    host = fields.String(default="127.0.0.1")
    port = fields.Integer(default=16000)
    enable_system_actor = fields.Boolean(default=True)
    _actors = fields.Typed(dict, default={})

    def __init__(self):
        super().__init__()
        self._core_actor = CoreActor(self)
        self._system_actor = SystemActor(self)
        self._loaded_actors = {"core": self._core_actor}

    @property
    def actors(self):
        """Lists saved actors
        
        Returns:
            list -- List of saved actors
        """
        return self._actors

    def actor_add(self, actor_name: str, actor_path: str):
        """Adds an actor to the server
        
        Arguments:
            actor_name {str} -- Actor name
            actor_path {str} -- Actor absolute path
        
        Raises:
            j.exceptions.Value: raises if actor name is matched one of the reserved actor names
            j.exceptions.Value: raises if actor name is not a valid identifier
        """
        if actor_name in RESERVED_ACTOR_NAMES:
            raise j.exceptions.Value("Actor name should be in {}".format(",".join(RESERVED_ACTOR_NAMES)))

        if not actor_name.isidentifier():
            raise j.exceptions.Value("Actor name should be a valid identifier")

        self._actors[actor_name] = actor_path

    def actor_delete(self, actor_name: str):
        """Removes an actor from the server
        
        Arguments:
            actor_name {str} -- Actor name
        """
        self._actors.pop(actor_name, None)

    def start(self):
        """Starts the server
        """
        j.application.start("gedis")

        # handle signals
        for signal_type in (SIGTERM, SIGTERM, SIGKILL):
            gevent.signal(signal_type, self.stop)

        # register system actor if enabled
        if self.enable_system_actor:
            self._register_actor("system", self._system_actor)

        # register saved actors
        for actor_name, actor_path in self._actors.items():
            self._system_actor.register_actor(actor_name, actor_path)

        # start the server
        server = StreamServer((self.host, self.port), self._on_connection)
        server.reuse_addr = True
        server.serve_forever()

    def stop(self):
        """Stops the server
        """
        j.logger.info("Shutting down ...")
        self._server.stop()

    def _register_actor(self, actor_name: str, actor_module: BaseActor):
        self._loaded_actors[actor_name] = actor_module

    def _unregister_actor(self, actor_name: str):
        self._loaded_actors.pop(actor_name, None)

    def _validate_method_arguments(self, method, args, kwargs):
        signature = inspect.signature(method)
        bound_arguments = signature.bind(*args, **kwargs)
        for name, value in bound_arguments.arguments.items():
            annotation = signature.parameters[name].annotation
            if not annotation.__module__ == "builtins":
                if isinstance(value, dict):
                    if 'from_dict' in dir(annotation):
                        annotation_object = annotation()
                        annotation_object.from_dict(value)
                        bound_arguments.arguments[name] = annotation_object

            if not isinstance(bound_arguments.arguments[name], annotation):
                raise j.exceptions.Validation(
                    f"parameter ({name}) supposed to be of type ({annotation.__name__}), but found ({type(value).__name__})"
                )

        return bound_arguments.args, bound_arguments.kwargs

    def _exceute(self, actor_name, method_name, args, kwargs):
        result = error = None
        actor = self._loaded_actors[actor_name]
        method = getattr(actor, method_name)
        try:
            args, kwargs = self._validate_method_arguments(method, args, kwargs)
            result = method(*args, **kwargs)

            if isinstance(result, bytes):
                result = result.decode()

            elif not type(result).__module__ == "builtins":
                result = result.to_dict()
        
        except j.exceptions.Validation as e:
            error = str(e)

        except Exception:
            error = better_exceptions.format_exception(*sys.exc_info())

        return result, error

    def _on_connection(self, socket, address):
        j.logger.info("New connection from {}", address)
        parser = DefaultParser(65536)
        connection = RedisConnectionAdapter(socket)
        try:
            encoder = ResponseEncoder(socket)
            parser.on_connect(connection)

            while True:
                try:
                    response = parser.read_response()
                    output = dict(success=True, error=None, result=None)
                    args = kwargs = None

                    if len(response) < 2:
                        output["error"] = "Invalid request"
                    else:
                        actor_name = response.pop(0).decode()
                        method_name = response.pop(0).decode()

                        if response:
                            args, kwargs = json.loads(response.pop(0))

                        args = args or ()
                        kwargs = kwargs or {}

                        if actor_name not in self._loaded_actors:
                            output["error"] = "Actor not loaded"
                        else:
                            j.logger.info(
                                "Executing method {} from actor {} to client {}", method_name, actor_name, address
                            )
                            output["result"], output["error"] = self._exceute(actor_name, method_name, args, kwargs)

                except ConnectionError:
                    j.logger.info("Client {} closed the connection", address)

                except Exception as err:
                    j.logger.exception(err, exception=err)
                    output["error"] = "Internal error"

                output["success"] = output["error"] is None
                encoder.encode(json.dumps(output))

            parser.on_disconnect()

        except BrokenPipeError:
            pass
