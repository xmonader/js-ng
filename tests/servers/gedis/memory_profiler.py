from jumpscale.servers.gedis.baseactor import BaseActor
from objgraph import count, show_most_common_types


class MemoryProfiler(BaseActor):

    def object_count(self, name):
        """returns number of instances in memory
        """
        return count(name.decode())
    
    def print_top_types(self, limit):
        show_most_common_types(limit=int(limit))


Actor = MemoryProfiler
