import os
import sys
import json
import inspect
from jumpscale.god import j
from jumpscale.servers.gedis.baseactor import BaseActor, actor_method


class CoreActor(BaseActor):
    def __init__(self, server):
        self.server = server

    def list_actors(self) -> list:
        """List available actors
        
        Returns:
            list -- list of available actors
        """
        return list(self.server._loaded_actors.keys())


class SystemActor(BaseActor):
    def __init__(self, server):
        self.server = server

    @actor_method
    def register_actor(self, actor_name: str, actor_path: str) -> bool:
        """Register new actor
        
        Arguments:
            actor_name {str} -- actor name within gedis server.
            actor_path {str} -- actor path on gedis server machine.
        
        Returns:
            bool -- True if registered.
        """
        module = j.tools.codeloader.load_python_module(actor_path)
        actor = module.Actor()
        result = actor.__validate_actor__()

        if not result["valid"]:
            raise j.exceptions.Validation(
                "Actor {} is not valid, check the following errors {}".format(actor_name, result["errors"])
            )

        self.server._register_actor(actor_name, actor)
        return True

    @actor_method
    def unregister_actor(self, actor_name: str) -> bool:
        """Register actor
        
        Arguments:
            actor_name {str} -- actor name
        
        Returns:
            bool -- True if actors is unregistered
        """
        self.server._unregister_actor(actor_name)
        return True
