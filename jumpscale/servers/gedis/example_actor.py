from jumpscale.servers.gedis.baseactor import BaseActor
from typing import Sequence
from jumpscale.god import j
import inspect, sys

class TestObject:
    def __init__(self):
        self.attr = None

    def to_dict(self):
        return self.__dict__

    def from_dict(self, ddict):
        self.__dict__ = ddict


class Example(BaseActor):
    def add_two_ints(self, x: int, y: int) -> int:
        """Adds two ints
        
        Arguments:
            x {int} -- first int
            y {int} -- second int
        
        Returns:
            int -- the sum of the two ints
        """
        return x + y

    def concate_two_strings(self, x: str, y: str) -> str:
        """Concate two strings
        
        Arguments:
            x {str} -- first string
            y {str} -- second string
        
        Returns:
            str -- the concate of the two strings
        """
        return x + y

    def modify_object(self, myobj: TestObject, new_value: int) -> TestObject:
        """Modify atrribute attr of the given object
        
        Arguments:
            myobj {TestObject} -- the object to be modified
        
        Returns:
            TestObject -- modified object
        """
        myobj.attr = new_value
        return myobj

Actor = Example
