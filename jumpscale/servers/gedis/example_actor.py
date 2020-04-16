from jumpscale.servers.gedis.baseactor import BaseActor


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


Actor = Example
