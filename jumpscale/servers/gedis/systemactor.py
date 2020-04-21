from .baseactor import BaseActor
import importlib
import os
import sys
import json

class SystemActor(BaseActor):
    def __init__(self, server):
        self.server = server

    def list_actors(self):
        return self.server.actors

    def remove_actor(self, actor_name):
        return self.server.actor_delete(actor_name)

    def register_actor(self, actor_name: str, actor_path: str) -> bool:
        """Register new actor
        
        Arguments:
            actor_name {str} -- actor name within gedis server.
            actor_path {str} -- actor path on gedis server machine.
        
        Returns:
            bool -- True if registered.
        """

        actor_name = actor_name.decode()
        actor_path = actor_path.decode()

        if actor_name in self.server.actors:
            return 1

        module_python_name = os.path.dirname(actor_path)
        module_name = os.path.splitext(module_python_name)[0]
        spec = importlib.util.spec_from_file_location(module_name, actor_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        self.server.actor_add(actor_name, module.Actor())

        return 1
