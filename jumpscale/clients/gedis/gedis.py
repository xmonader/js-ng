from jumpscale.clients.base import Client
from jumpscale.core.base import fields
from jumpscale.god import j
from functools import update_wrapper, partial
import json
from typing import List
import codecs
import pickle


types = {
    "int": int,
    "str": str,
    "float": float,
    "bool": bool,
    "set": set,
    "bytes": bytes,
    "complex": complex,
    "list": list,
    "dict": dict,
    "tuple": tuple,
    "callable": callable,
}


class ActorProxy:
    def __init__(self, actor_name, actor_info, gedis_client):
        """ActorProxy to remote actor on the server side

        Arguments:
            actor_name {str} -- [description]
            actor_info {dict} -- actor information dict e.g { method_name: { args: [], 'doc':...} }
            gedis_client {GedisClient} -- gedis client reference
        """
        self.actor_name = actor_name
        self.actor_info = actor_info
        self._gedis_client = gedis_client

    def _map_inputs(self, actor_name, method_name, *args, **kwargs):
        signature_blob = self.actor_info[method_name]["signature"]

        signature = pickle.loads(codecs.decode(signature_blob, "hex"))
        binded = signature.bind(*args, **kwargs)

        # import ipdb; ipdb.set_trace()



        return binded.args, binded.kwargs

        
        # new_args = []
        # new_kwargs = {}
        
        # for arg in func_spec["args"]:
        #     argname, argtype = arg

            





        # if not len(args) + len(kwargs) == len(func_args):
        #     raise j.exceptions.Value(
        #         f"invalid number of arguments, expected {len(func_args)} but got {len(args)}"
        #     )

        # if kwargs:
        #     func_args_names = [x[0] for x in func_args]
        #     for key in kwargs.keys():
        #         if key not in func_args_names:
        #             raise j.exceptions.Value(f"got an unexpected keyword argument {key}")

        # if not len(args) + len(kwargs) == len(func_args):
        #     raise j.exceptions.Value(
        #         f"invalid number of arguments, expected {len(func_args)} but got {len(args)}"
        #     )

        # for i, arg in enumerate(args):
        #     arg_type = type(arg).__name__
        #     func_arg_name, func_arg_type = func_args[i]

        #     if func_arg_type and func_arg_type != arg_type:
        #         validation_errors.append(
        #             f"argument {func_arg_name} is supposed to be {func_arg_type}, but got {arg_type}"
        #         )
        
        # if validation_errors:
        #     raise j.exceptions.Value('\n'.join(validation_errors))


    def __dir__(self):
        """Delegate the available functions on the ActorProxy to `actor_info` keys

        Returns:
            list -- methods available on the ActorProxy
        """
        return list(self.actor_info.keys())

    def __getattr__(self, attr):
        """Return a function representing the remote function on the actual actor

        Arguments:
            attr {str} -- method name

        Returns:
            function -- function waiting on the arguments
        """

        def mkfun(actor_name, fn_name, *args, **kwargs):
            payload = {"args": args, "kwargs": kwargs}
            return self._gedis_client.execute(actor_name, fn_name, json.dumps(payload, default=lambda o: o.to_dict()))

        func = partial(mkfun, self.actor_name, attr)
        func.__doc__ = self.actor_info[attr]["doc"]
        return func


class ActorsCollection:
    def __init__(self, gedis_client):
        """ActorsCollection to allow using the actors like `gedis.actors.ACTORNAME.ACTORMETHOD(*ACTOR_METHOD_ARGS)

        Arguments:
            gedis_client {GedisClient} -- gedis client
        """
        self._gedis_client = gedis_client
        self._actors = {}
        self._load_all_actors()

    def __dir__(self):
        return list(self._actors.keys())

    def __getattr__(self, actor_name):
        if actor_name in self._actors:
            return self._actors[actor_name]

    @property
    def actors_names(self):
        return self._gedis_client.execute("core", "list_actors")

    def _load_actor(self, actor_name):
        if actor_name in self.actors_names:
            actor_info = self._gedis_client.execute(actor_name, "info")
            self._actors[actor_name] = ActorProxy(actor_name, actor_info, self._gedis_client)

    def _load_all_actors(self):
        """Load actor: creating ActorProxy for remote actor `actor_name` and store it in the collection.

        Arguments:
            actor_name {str} -- remote actor name

        Returns:
            ActorProxy -- ActorProxy that can call the remote actor.
        """
        for actor_name in self.actors_names:
            actor_info = self._gedis_client.execute(actor_name, "info")
            self._actors[actor_name] = ActorProxy(actor_name, actor_info, self._gedis_client)


class GedisClient(Client):
    name = fields.String(default="local")
    hostname = fields.String(default="localhost")
    port = fields.Integer(default=16000)

    def __init__(self):
        super().__init__()
        self._redisclient = None
        self.redis_client
        self.actors = ActorsCollection(self)

    @property
    def redis_client(self):
        if not self._redisclient:
            try:
                self._redisclient = j.clients.redis.get(f"gedis_{self.name}")
            except:
                self._redisclient = j.clients.redis.new(f"gedis_{self.name}")

        self._redisclient.hostname = self.hostname
        self._redisclient.port = self.port
        self._redisclient.save()
        return self._redisclient

    def execute(self, actor_name: str, actor_method: str, *args):
        """Execute

        Arguments:
            actor_name {str} -- actor name
            actor_name {str} -- actor method to execute
            *args      {List[object]}  -- *args of parameters

        """
        response = self._redisclient.execute_command(actor_name, actor_method, *args)
        response_json = json.loads(response.decode())

        if response_json["success"]:
            return response_json["result"]
        
        print(response_json["error"])
        # raise RemoteException(response_json["error"])

    def doc(self, actor_name: str):
        """Gets the documentation of actor `actor_name`

        Arguments:
            actor_name {str} -- actor to retrieve its documentation

        """
        return self.execute(actor_name, "info")

    def ppdoc(self, actor_name):
        """Pretty print documentation of actor

        Arguments:
            actor_name {str} -- actor to print its documentation.
        """
        docs = self.doc(actor_name)
        print(json.dumps(docs, indent=2, sort_keys=True))

    def register_actor(self, actor_name: str, actor_path: str):
        """Register actor on the server side (gedis server)

        Arguments:
            actor_name {str} -- actor name to be used in the system
            actor_path {str} -- actor path on the remote gedis server

        """
        if "system" not in self.actors.actors_names:
            raise j.exceptions.NotImplemented("Gedis server doesn't support registering actors")

        response = self.execute("system", "register_actor", actor_name, actor_path)
        if response:
            self.actors._load_actor(actor_name)

    def list_actors(self) -> List[str]:
        """List actors

        Returns:
            List[str] -- list of actors available on gedis server.
        """
        return self.execute("core", "list_actors")

    def reload(self):
        self.actors._load_all_actors()

    def validate_actor(self, actor_path: str):
        """Validate actor

        Arguments:
            actor_path {str} -- actor absolute path
        """
        


class RemoteException(Exception):
    pass
