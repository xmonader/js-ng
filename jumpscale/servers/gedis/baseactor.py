import inspect
import json
import codecs
import pickle
import sys


class BaseActor:
    def info(self) -> dict:
        info = {}
        info["module"] = self.__module__
        info["path"] = sys.modules[self.__class__.__module__].__file__
        info["methods"] = {}

        methods = inspect.getmembers(self, predicate=inspect.ismethod)
        for name, attr in methods:
            if name.startswith("_"):
                continue

            signature = inspect.signature(attr)
            info["methods"][name] = {}
            info["methods"][name]["args"] = []


            result_type = signature.return_annotation
            if result_type is inspect._empty:
                result_type = type(None)

            if inspect.isclass(signature.return_annotation):
                result_type = signature.return_annotation.__name__

            info["methods"][name]["result_type"] = result_type
            info["methods"][name]["doc"] = attr.__doc__ or ""

            for parameter_name, parameter in signature.parameters.items():
                info["methods"][name]["args"].append((parameter_name, parameter.annotation.__name__))

        return info

    @property
    def __weakref__(self):
        return self.__wrapped__.__weakref__

    def __validate_actor__(self):
        TYPES = [str, int, float, list, tuple, dict, bool]

        def validate_annotation(annotation, annotated):
            if annotation is None or annotation is inspect._empty:
                return

            if not (inspect.isclass(annotation) and annotation.__class__ == type):
                raise ValueError("annotation must be a class type")

            if annotation not in TYPES:
                if annotation.__module__ == "builtins":
                    raise ValueError(f"unsupported type ({annotation.__name__})")

                for method in ["to_dict", "from_dict"]:
                    if method not in dir(annotation):
                        raise ValueError(
                            f"type ({annotation.__name__}) which annotate {annotated} doesn't have {method} method"
                        )

        result = {"valid": True, "errors": {}}
        methods = inspect.getmembers(self, predicate=inspect.ismethod)
        for method_name, method_callable in methods:
            if method_name.startswith("_"):
                continue

            result["errors"][method_name] = []
            signature = inspect.signature(method_callable)
            try:
                validate_annotation(signature.return_annotation, "return")
            except ValueError as e:
                result["errors"][method_name].append(str(e))

            for name, parameter in signature.parameters.items():
                try:
                    validate_annotation(parameter.annotation, f"parameter ({name})")
                except ValueError as e:
                    result["errors"][method_name].append(str(e))

        if any(result["errors"].values()):
            result["valid"] = False

        return result
