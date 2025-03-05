from .umqtt import load_stub as umqtt_stub
from .network import load_stub as network_stub
from .time import load_stub as time_stub

def init_all_stubs():
    umqtt_stub()
    network_stub()
    time_stub()
