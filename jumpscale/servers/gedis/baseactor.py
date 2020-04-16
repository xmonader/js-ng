import inspect
import json
import codecs
import pickle


class BaseActor:
    def info(self) -> dict:
        result = {}
        # methods = inspect.getmembers(self, predicate=inspect.ismethod)
        # for name, attr in methods:
        #     if name.startswith("_"):
        #         continue

            # result[name] = {}
            # result[name]["doc"] = attr.__doc__ or ""

            # spec = inspect.getfullargspec(attr)
            # signature = inspect.signature(attr)
            # result[name]["signature"] = codecs.encode(pickle.dumps(signature), "hex").decode()
            # result[name]["spec"] = {}
            # result[name]["spec"]["varargs"] = spec.varargs
            # result[name]["spec"]["varkw"] = spec.varkw
            # result[name]["spec"]["args"] = []
            # for arg_name in spec.args[1:]:
            #     arg_type = spec.annotations.get(arg_name)
            #     if arg_type:
            #         arg_type = arg_type.__name__

            #     result[name]["spec"]["args"].append((arg_name, arg_type))

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
                result["errors"][method_name].append(
                    f"method doesn't have return type annotation"
                )
            elif not signature.return_annotation.__module__ == "builtins":
                _validate_annotation(method_name, "methods' return", signature.return_annotation)

            for parameter_name, parameter in signature.parameters.items():
                if parameter.annotation is inspect._empty:
                    result["errors"][method_name].append(
                        f"parameter ({parameter_name}) doesn't have type annotation"
                    )
                elif not parameter.annotation.__module__ == "builtins":
                    _validate_annotation(method_name, f"parameter {parameter_name}", parameter.annotation)

        if any(result["errors"].values()):
            result["valid"] = False

        return result