import inspect
import json
import codecs
import pickle

class BaseActor:
    def info(self) -> dict:
        result = {}
        members = inspect.getmembers(self)
        for name, attr in members:
            if inspect.ismethod(attr):
                result[name] = {}
                result[name]["doc"] = attr.__doc__ or ""

                spec = inspect.getfullargspec(attr)
                signature = inspect.signature(attr)
                result[name]["signature"] = codecs.encode(pickle.dumps(signature), "hex").decode()
                result[name]["spec"] = {}
                result[name]["spec"]["varargs"] = spec.varargs
                result[name]["spec"]["varkw"] = spec.varkw
                result[name]["spec"]["args"] = []
                for arg_name in spec.args[1:]:
                    arg_type = spec.annotations.get(arg_name)
                    if arg_type:
                        arg_type = arg_type.__name__

                    result[name]["spec"]["args"].append((arg_name, arg_type))
                

        return result
