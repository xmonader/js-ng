import codecs
import inspect
import json
import os
import pickle
import sys
from functools import partial, update_wrapper
from typing import List

from jumpscale.clients.base import Client
from jumpscale.core.base import fields
from jumpscale.god import j
from jumpscale.tools.codeloader import load_python_module
from jumpscale.servers.gedis.server import GedisErrorTypes


class ActorResult:
    def __init__(self, **kwargs):
        self.success = kwargs.get("success", True)
        self.result = kwargs.get("result", None)
        self.error = kwargs.get("error", None)
        self.error_type = kwargs.get("error_type", None)

    def __dir__(self):
        return list(self.__dict__.keys())


class ActorProxy:
    def __init__(self, actor_name, actor_info, client):
        """ActorProxy to remote actor on the server side

        Arguments:
            actor_name {str} -- [description]
            actor_info {dict} -- actor information dict e.g { method_name: { args: [], 'doc':...} }
            gedis_client {GedisClient} -- gedis client reference
        """
        self.actor_name = actor_name
        self.actor_info = actor_info
        self.client = client
        self.module = sys.modules.get(self.actor_info["module"])

    def __dir__(self):
        """Delegate the available functions on the ActorProxy to `actor_info` keys

        Returns:
            list -- methods available on the ActorProxy
        """
        return list(self.actor_info["methods"].keys())

    def __getattr__(self, method):
        """Return a function representing the remote function on the actual actor

        Arguments:
            attr {str} -- method name

        Returns:
            function -- function waiting on the arguments
        """

        def function(*args, **kwargs):
            return self.client.execute(self.actor_name, method, *args, **kwargs)

        func = partial(function)
        func.__doc__ = self.actor_info["methods"][method]["doc"]
        return func


class ActorsCollection:
    def __init__(self, actors):
        self._actors = actors

    def __dir__(self):
        return list(self._actors.keys())

    def __getattr__(self, actor_name):
        if actor_name in self._actors:
            return self._actors[actor_name]


class GedisClient(Client):
    name = fields.String(default="local")
    hostname = fields.String(default="localhost")
    port = fields.Integer(default=16000)

    def __init__(self):
        super().__init__()
        self._redisclient = None
        self._loaded_actors = {}
        self._loaded_modules = set()
        self._actors_load()
        self.actors = ActorsCollection(self._loaded_actors)

    @property
    def redis_client(self):
        if self._redisclient is None:
            self._redisclient = j.clients.redis.get(name=f"gedis_{self.name}", hostname=self.hostname, port=self.port)
        return self._redisclient

    def _module_load(self, path):
        if path not in self._loaded_modules:
            load_python_module(path)
            self._loaded_modules.add(path)

    def _actors_load(self):
        for actor_name in self.actors_list():
            actor_info = self.actor_info(actor_name)
            self._module_load(actor_info["path"])
            self._loaded_actors[actor_name] = ActorProxy(actor_name, actor_info, self)

    def actors_list(self) -> list:
        """Lists actors
        
        Returns:
            list -- list of actors
        """
        return self._execute("core", "list_actors")["result"]

    def actor_info(self, actor_name):
        return self._execute(actor_name, "info")["result"]

    def _execute(self, actor_name: str, actor_method: str, *args, die: bool = True, **kwargs) -> dict:
        payload = json.dumps((args, kwargs), default=lambda o: o.to_dict())
        response = self.redis_client.execute_command(actor_name, actor_method, payload)
        response = json.loads(response.decode())

        if not response["success"] and die:
            raise RemoteException(response["error"])

        return response

    def execute(self, actor_name: str, actor_method: str, *args, **kwargs) -> dict:
        actor = self._loaded_actors.get(actor_name)
        if not actor:
            raise j.exceptions.NotFound(f"Actor {actor_name} is not loaded")

        method = actor.actor_info["methods"].get(actor_method)
        if not method:
            raise j.exceptions.Value(f"Actor {actor_name} doesn't have method {actor_method}")

        response = self._execute(actor_name, actor_method, *args, die=False, **kwargs)
        result = response["result"]
        result_type_name = method["result_type"]
        return_type = actor.module.__dict__.get(result_type_name) or actor.module.__builtins__.get(result_type_name)

        if return_type and not isinstance(result, return_type):
            if hasattr(return_type, "from_dict"):
                result_object = return_type()
                result_object.from_dict(result)
                result = result_object

        response["result"] = result
        if response["error_type"]:
            response["error_type"] = GedisErrorTypes(response["error_type"])
        return ActorResult(**response)


class RemoteException(Exception):
    pass
