from jumpscale.servers.gedis.baseactor import BaseActor
from typing import Sequence


class Hamada:
    def __init__(self):
        self.x = 1

    def to_dict(self):
        return self.__dict__

    def from_dict(self, d):
        self.__dict__ = d


class Example(BaseActor):
    def add_two_ints(self, x: int, y: Hamada):
        """Adds two ints
        
        Arguments:
            x {int} -- first int
            y {int} -- second int
        
        Returns:
            int -- the sum of the two ints
        """
        return y

    def concate_two_strings(self, x: str, y) -> str:
        """Concate two strings
        
        Arguments:
            x {str} -- first string
            y {str} -- second string
        
        Returns:
            str -- the concate of the two strings
        """
        return x + y

Actor = Example
