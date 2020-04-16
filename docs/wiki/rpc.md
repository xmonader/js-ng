# Gedis
Gedis is a RPC framework that provide automatic generation of client side code at runtime.
Which means you only need to define the server interface and the client will automatically receive the code it needs to talk to the server at connection time.


## Gedis Actor
The ```Gedis``` actors should inherts from the ```BaseActor``` class and all function should define the type annotations of its parameters

```python
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
```

### Starting the server and loading actors
``` python
JS-NG> server = j.servers.gedis.get("main")
JS-NG> server.actor_add("example", "/sandbox/code/github/js-next/js-ng/jumpscale/servers/gedis/example_actor.py")
JS-NG> server.start()
```

### Getting a client and calling actors
```python
JS-NG> cl = j.clients.gedis.get("main")
JS-NG> cl.actors.example.add_two_ints(1, 2)
3
```

> in case the actor method is missing the type annotation of one of its parameters, the server will return an error for example ```jumpscale.core.exceptions.exceptions.Runtime: argument x in method add_two_ints doesn't have type annotation```
