from jumpscale.god import j


class DockerFactory:
    def __init__(self):
        pass

    # def __dir__(self):
    #     return ("get", "find", "alert_raise", "count", "reset", "delete", "delete_all")

    def echo(self):
        a = 1
        j.debug()
        
        print(1)
