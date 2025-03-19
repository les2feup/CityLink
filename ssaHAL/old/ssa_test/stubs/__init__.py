from .umqtt import load_stub as umqtt_stub
from .network import load_stub as network_stub
from .time import load_stub as time_stub


def init_all_stubs():
    """
    Initialize all stub modules.

    Calls the umqtt, network, and time stub initialization functions to set up
    the testing environment.
    """
    umqtt_stub()
    network_stub()
    time_stub()
