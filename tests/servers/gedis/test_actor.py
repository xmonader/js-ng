from jumpscale.servers.gedis.baseactor import BaseActor
from jumpscale.god import j
import inspect, sys


class ValidObject:
    def __init__(self):
        self.attr = None

    def to_dict(self):
        return self.__dict__

    def from_dict(self, ddict):
        self.__dict__ = ddict


class InvalidObject1:
    def __init__(self):
        self.attr = None

    def to_dict(self):
        return self.__dict__


class InvalidObject2:
    def __init__(self):
        self.attr = None

    def from_dict(self, ddict):
        self.__dict__ = ddict


class TestActor(BaseActor):

    def sum_two_ints(self, x: int, y: int) -> int:
        return x + y

    def concate_two_strings(self, x: str, y: str) -> str:
        return x + y

    def modify_object(self, obj: ValidObject, new_value: int) -> ValidObject:
        obj.attr = new_value
        return obj

    def none_return(self) -> None:
        return 

    def without_return_annotation(self):
        return

    def return_different_type(self) -> int:
        return 'string'

    def return_different_un_serializable_type(self) -> int:
        return ValidObject()

Actor = TestActor
    
#     def add_two_ints(self, x: int, y: int) -> int:
#         """Adds two ints
        
#         Arguments:
#             x {int} -- first int
#             y {int} -- second int
        
#         Returns:
#             int -- the sum of the two ints
#         """
#         return x + "s"

#     def concate_two_strings(self, x: str, y: str) -> str:
#         """Concate two strings
        
#         Arguments:
#             x {str} -- first string
#             y {str} -- second string
        
#         Returns:
#             str -- the concate of the two strings
#         """
#         return TestObject()

#     def modify_object(self, myobj: TestObject, new_value: int) -> TestObject:
#         """Modify atrribute attr of the given object
        
#         Arguments:
#             myobj {TestObject} -- the object to be modified
        
#         Returns:
#             TestObject -- modified object
#         """
#         myobj.attr = new_value
#         return myobj


# Actor = Example
