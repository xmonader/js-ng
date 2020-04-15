from jumpscale.servers.gedis.baseactor import BaseActor
import time

class Greeter(BaseActor):
    def hi(self):
        """returns hello world
        """
        return "hello world"

    def ping(self):
        """
        
        """
        return "pong no?"

    def add2(self, a, b):
        """Add two args
        """
        return int(a) + int(b)


Actor = Greeter
