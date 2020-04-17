import inspect
import json
import codecs
import pickle
import sys



class BaseActor:
    def info(self) -> dict:
        result = {"path": sys.modules[self.__class__.__module__].__file__ , "module": self.__module__}
        methods = inspect.getmembers(self, predicate=inspect.ismethod)
        for name, attr in methods:
            if name.startswith("_"):
                continue
            
            signature = inspect.signature(attr)
            result[name] = {}
            result[name]["doc"] = attr.__doc__ or ""
            result[name]["args"] = []

            response_type = None
            if signature.return_annotation:
                if not signature.return_annotation.__module__ == "builtins":
                    response_type = signature.return_annotation.__name__

            result[name]["response_type"] = response_type



            #  parameter.annotation.__module__ == "builtins"

            # if signature.return_annotation:
            #     result[name]["response_type"] = signature.return_annotation.__name__
            # else:
            #     result[name]["response_type"] = signature.return_annotation

            

            # for parameter_name, parameter in signature.parameters.items():
            #     result[name]["args"].append((parameter_name, parameter.annotation.__name__))

        return result

    def __validate_actor__(self):
        def _validate_annotation(method_name, title, annotation):
            if "from_dict" not in dir(annotation):
                result["errors"][method_name].append(
                    f"type ({annotation.__name__}) which annotates ({title}) doesn't have from_dict method"
                )
            if "to_dict" not in dir(annotation):
                result["errors"][method_name].append(
                    f"type ({annotation.__name__}) which annotates ({title}) doesn't have to_dict method"
                )

        result = {"valid": True, "errors": {}}
        methods = inspect.getmembers(self, predicate=inspect.ismethod)
        for method_name, attr in methods:
            if method_name.startswith("_"):
                continue

            result["errors"][method_name] = []
            signature = inspect.signature(attr)
            if signature.return_annotation is inspect._empty:
                result["errors"][method_name].append(f"method doesn't have return type annotation")
            elif signature.return_annotation and not signature.return_annotation.__module__ == "builtins" :
                _validate_annotation(method_name, "methods' return", signature.return_annotation)

            for parameter_name, parameter in signature.parameters.items():
                if parameter.annotation is inspect._empty:
                    result["errors"][method_name].append(f"parameter ({parameter_name}) doesn't have type annotation")
                elif not parameter.annotation.__module__ == "builtins":
                    _validate_annotation(method_name, f"parameter {parameter_name}", parameter.annotation)

        if any(result["errors"].values()):
            result["valid"] = False

        return result
