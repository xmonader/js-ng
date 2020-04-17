import inspect
import json
import sys
from enum import Enum
from functools import partial
from io import BytesIO
from signal import SIGKILL, SIGTERM

import better_exceptions
import gevent
from gevent import time
from gevent.pool import Pool
from gevent.server import StreamServer
from jumpscale.core.base import Base, fields
from jumpscale.god import j
from redis.connection import DefaultParser, Encoder
from redis.exceptions import ConnectionError

from .baseactor import BaseActor
from .systemactor import CoreActor, SystemActor


class GedisErrorTypes(Enum):
    NOT_FOUND = 0
    BAD_REQUEST = 1
    ACTOR_ERROR = 2
    INTERNAL_SERVER_ERROR = 3


class RedisConnectionAdapter:
    def __init__(self, sock):
        self.socket = sock
        self._sock = sock
        self.socket_timeout = 600
        self.socket_connect_timeout = 600
        self.socket_keepalive = True
        self.retry_on_timeout = True
        self.socket_keepalive_options = {}
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


SERIALIZABLE_TYPES = (str, int, float, list, tuple, dict, bool)
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
        try:
            bound = signature.bind(*args, **kwargs)
        except TypeError as e:
            raise j.exceptions.Validation(e)

        for name, val in bound.arguments.items():
            annotation = signature.parameters[name].annotation
            if not isinstance(val, annotation):
                if hasattr(annotation, "from_dict"):
                    argument_object = annotation()
                    argument_object.from_dict(val)  
                    bound.arguments[name] = argument_object
                else:
                    raise j.exceptions.Validation(
                       f"parameter ({name}) supposed to be of type ({annotation}), but found ({type(val)})"
                    )

        return_type = signature.return_annotation
        if return_type in (None, inspect._empty):
            return_type = type(None)

        return bound.args, bound.kwargs, return_type

    def _exceute(self, actor_name, method_name, args, kwargs):
        result = error = error_type = None
        actor = self._loaded_actors[actor_name]
        method = getattr(actor, method_name)
        try:
            args, kwargs, return_type = self._validate_method_arguments(method, args, kwargs)
            result = method(*args, **kwargs)

            if isinstance(result, return_type):
                if return_type not in SERIALIZABLE_TYPES:
                    if hasattr(result, "to_dict"):
                        result = result.to_dict()
                    else:
                        j.exceptions.Value("Failed to serialize response result")
            else:
                message = f"method {actor_name}:{method_name} is supposed to return ({return_type}), but it returned ({type(result)})"
                if isinstance(result, SERIALIZABLE_TYPES):
                    j.logger.warning(message)
                else:
                    result = None
                    raise j.exceptions.Value(message)

        except j.exceptions.Validation as e:
            error = str(e)
            error_type = GedisErrorTypes.BAD_REQUEST.value

        except:
            ttype, tvalue, tb = sys.exc_info()
            error = better_exceptions.format_exception(ttype, tvalue, tb.tb_next)
            error_type = GedisErrorTypes.ACTOR_ERROR.value

        return result, error, error_type

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
                    output = dict(success=True, result=None, error=None, error_type=None)
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
                            output["error"] = "actor not found"
                            output["error_type"] = GedisErrorTypes.ACTOR_ERROR.value

                        else:
                            j.logger.info(
                                "Executing method {} from actor {} to client {}", method_name, actor_name, address
                            )
                            output["result"], output["error"], output["error_type"] = self._exceute(
                                actor_name, method_name, args, kwargs
                            )

                except ConnectionError:
                    j.logger.info("Client {} closed the connection", address)

                except Exception as execption:
                    j.logger.execption("internal error", execption=execption)
                    output["error"] = "internal server error"
                    output["error_type"] = GedisErrorTypes.INTERNAL_SERVER_ERROR.value

                output["success"] = output["error"] is None
                encoder.encode(json.dumps(output))

            parser.on_disconnect()

        except BrokenPipeError:
            pass
