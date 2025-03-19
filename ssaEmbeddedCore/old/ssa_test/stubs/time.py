import sys
from types import ModuleType


def load_stub():
    """
    Initializes a stub implementation for the 'time' module.

    If the 'time' module is not present in sys.modules, this function creates a new module
    with a no-operation sleep function and registers it. If the module already exists,
    it updates its sleep function to perform no operation and adds a sleep_ms function,
    both annotated with documentation indicating they are stub implementations.
    """
    if "time" not in sys.modules:
        time_stub = ModuleType("time")
        time_stub.sleep = lambda x: None
        sys.modules["time"] = time_stub
    else:
        time_mod = sys.modules["time"]
        time_mod.sleep = lambda x: None
        time_mod.sleep.__doc__ = (
            "Stub implementation of time.sleep that performs no operation."
        )
        time_mod.sleep_ms = lambda x: None
        time_mod.sleep_ms.__doc__ = (
            "Stub implementation of time.sleep_ms that performs no operation."
        )
        sys.modules["time"] = time_mod
