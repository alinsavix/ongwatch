import argparse
import importlib
import logging
from types import ModuleType
from typing import Callable, Coroutine, Dict

# FIXME: Probably need a 'Backend' protocol?
BackendAuthHandler = Callable[[argparse.Namespace, Dict[str, str]
                               | None, logging.Logger], Coroutine[None, None, bool]]
BackendStartHandler = Callable[[argparse.Namespace, Dict[str, str]
                                | None, logging.Logger], Coroutine[None, None, None]]

BACKEND_LIST = ["twitch", "streamelements", "streamlabs"]

def backend_list() -> list[str]:
    return BACKEND_LIST

# FIXME: Should we return the import, or should we return specific functions?
def get_backend(name: str) -> ModuleType:
    return importlib.import_module(f"_ongwatch.backends.{name}")
