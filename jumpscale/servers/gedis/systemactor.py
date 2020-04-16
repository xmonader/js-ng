from .baseactor import BaseActor
import importlib
import os
import sys
import json


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

    def register_actor(self, actor_name: str, actor_path: str) -> bool:
        """Register new actor
        
        Arguments:
            actor_name {str} -- actor name within gedis server.
            actor_path {str} -- actor path on gedis server machine.
        
        Returns:
            bool -- True if registered.
        """
        module_python_name = os.path.dirname(actor_path)
        module_name = os.path.splitext(module_python_name)[0]
        spec = importlib.util.spec_from_file_location(module_name, actor_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        self.server._register_actor(actor_name, module.Actor())
        return True

    def unregister_actor(self, actor_name: str) -> bool:
        """Register actor
        
        Arguments:
            actor_name {str} -- actor name
        
        Returns:
            bool -- True if actors is unregistered
        """
        self.server._unregister_actor(actor_name)
        return True
