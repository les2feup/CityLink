import sys
from types import ModuleType

def load_stub():
    if "time" not in sys.modules:
        time_stub = ModuleType("time")
        time_stub.sleep = lambda x: None
        sys.modules["time"] = time_stub
    else:
        time_mod = sys.modules["time"]
        time_mod.sleep = lambda x: None
        time_mod.sleep.__doc__ = "Stub implementation of time.sleep that performs no operation."
        time_mod.sleep_ms = lambda x: None
        time_mod.sleep_ms.__doc__ = "Stub implementation of time.sleep_ms that performs no operation."
        sys.modules["time"] = time_mod

