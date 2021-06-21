from enum import Enum, auto


class ConnectionType(Enum):
    """Enum to declare whether to use WAN or LAN. 

	 NOTE: It is almost always recommended to use LAN over WAN because it will be faster and use less resources however if you are running this node server on a different connection than your camera for whatever reason then you must use WAN
    """
    WAN = auto()
    LAN = auto()
