import os
import json
import asyncio

from time import sleep
from network import WLAN, STA_IF
from umqtt.simple import MQTTClient

from typing import Any, Dict, List, Tuple, Callable, Awaitable, Optional

def __singleton(cls):
    instance = None
    def getinstance(*args, **kwargs):
        nonlocal instance
        if instance is None:
            print("[DEBUG] SSA instance created")
            instance = cls(*args, **kwargs)
        return instance
    return getinstance

def __fw_update_callback(_ssa: 'SSA', update_str: str):
    print(f"[INFO] Firmware update received with size {len(update_str)}")
    update = json.loads(update_str)

    from binascii import crc32, a2b_base64

    binary = a2b_base64(update["base64"])
    expected_crc = int(update["crc32"], 16)
    bin_crc = crc32(binary)

    if bin_crc != expected_crc:
        print(f"[ERROR] CRC32 mismatch: expected:{hex(expected_crc)}, got {hex(bin_crc)} Firmware update failed.")
        return

    if "user" not in os.listdir():
        os.mkdir("user")

    print("[INFO] Writing firmware to device")
    with open("user/app.py", "w") as f:
        f.write(binary.decode("utf-8"))

    print("[INFO] Firmware write complete. Restarting device.")
    from machine import soft_reset
    soft_reset()

def __property_update_action(ssa: 'SSA', msg: str, prop: str):
    if prop not in ssa.__properties:
        print(f"[ERROR] Property `{prop}` does not exist. Create it using `create_property` before setting it.")
        return

    value = json.loads(msg)
    ssa.set_property(prop, value)

class ActDictElement():
    def __init__(self,
                 callback: Optional[Callable[['SSA', str, ...], None]] = None,
                 node_name: Optional[str] = None,
                 children: Optional[Dict[str, ActDictElement]] = None):

        self.callback = callback
        self.node_name = node_name
        self.children = children if children is not None else {}

@__singleton
class SSA():
    def __init__(self):
        self.UUID: str
        self.BASE_TOPIC: str
        self.BASE_ACTION_TOPIC: str
        self.REGISTRATION_TOPIC: str

        self.__wlan: WLAN | None = None
        self.__mqtt: MQTTClient | None = None

        self.__tasks: List[asyncio.Task] = []
        self.__action_cb_dict: Dict[str, ActDictElement] = {}

        self.__properties: Dict[str, Any] = {}

    #TODO: Make this function return config and secrets as separate dictionaries this function return config and secrets as separate dictionaries
    def __load_config(self) -> Dict[str, Any]:
        CONFIG_FILE_PATH = "../config/config.json"
        SECRETS_FILE_PATH = "../config/secrets.json"

        config: Dict[str, Any] = {}

        try:
            with open(CONFIG_FILE_PATH, "r") as config_file:
                config = json.load(config_file)
        except OSError as e:
            raise Exception(f"[ERROR] config.json could not be parsed: {e}") from e

        try:
            with open(SECRETS_FILE_PATH, "r") as secrets_file:
                config = config | json.load(secrets_file)
        except OSError as e:
            raise Exception(f"[ERROR] secrets.json could not be parsed: {e}") from e

        return config

    def __validate_config(self, CONFIG: Dict[str, Any]):
        try:
            # WIFI Config
            CONFIG["wifi"]
            CONFIG["wifi"]["ssid"]
            CONFIG["wifi"]["password"]

            # Broker Config
            CONFIG["broker"]
            CONFIG["broker"]["host"]
            CONFIG["broker"]["port"]

            # Self identification config
            CONFIG["self_id"]
            CONFIG["self_id"]["uuid"]
            CONFIG["self_id"]["model"]
            CONFIG["self_id"]["version"]
            CONFIG["self_id"]["version"]["instance"]
            CONFIG["self_id"]["version"]["model"]
        except Exception as e:
            raise Exception(f"[ERROR] malformed config: Missing \"{e}\" key") from e

        self.UUID = CONFIG["self_id"]["uuid"]
        self.BASE_TOPIC = f"{CONFIG["self_id"]['model']}/{self.UUID}"
        self.BASE_ACTION_TOPIC = f"{self.BASE_TOPIC}/actions"
        self.REGISTRATION_TOPIC = f"registration/{self.UUID}"

    def __wlan_connect(self, SSID: str, PASSWORD: str):
        #TODO: Check if already connected
        #TODO: Check if given SSID exits

        self.__wlan = WLAN(STA_IF)
        self.__wlan.active(True)
        self.__wlan.connect(SSID, PASSWORD)

        print("[INFO] connecting to WiFi...", end="")
        while not self.__wlan.isconnected():
            sleep(1)
            print(".", end="")
        print("\n[INFO] connected! IP Address:", self.__wlan.ifconfig()[0])

    def __mqtt_connect(self,
                       client_id: str,
                       broker: str,
                       port: int,
                       last_will: str | None = None):
        #TODO: Improve error handling
        #TODO: Add security

        self.__mqtt = MQTTClient(client_id, broker, port)

        if last_will is not None and len(last_will) > 0:
            topic = f"{self.BASE_TOPIC}/last_will",
            self.__mqtt.set_last_will(topic, last_will, qos=1)

        print("Attempting to connect to MQTT broker")
        self.__mqtt.connect()
        print("Connected to MQTT broker")

    def __extract_action_path(self, topic: str) -> Optional[str]:
        topic = topic.decode("utf-8")
        if topic.startswith(self.BASE_ACTION_TOPIC):
            return topic[len(self.BASE_ACTION_TOPIC) + 1:] # +1 to remove the trailing '/'
        return None

    def __find_action_callback(self, action: str, msg: str) -> Optional[Tuple[Callable[[SSA, str, Any], Dict[str, str]]]]:
        """
        Walks the action callback tree using the given action string.
        Returns a tuple (callback_function, kwargs) if a callback is found,
        or None if no callback matches the action.
        
        The kwargs dictionary maps URI parameter names to their corresponding values.
        For example, if the action "foo/{bar}/baz" is called with "foo/1123/baz",
        then kwargs will be {"bar": "1123"}.
        """
        parts = action.split("/")
        # The first part must be a literal.
        if parts[0] not in self.__action_cb_dict:
            return None

        current_node = self.__action_cb_dict[parts[0]]
        kwargs = {}  # dictionary to hold parameter values mapped by their node_name

        for part in parts[1:]:
            if current_node.children is None:
                return None
            # Check for a literal match first.
            if part in current_node.children:
                current_node = current_node.children[part]
            # If no literal match, try a parameter match.
            elif "*" in current_node.children:
                current_node = current_node.children["*"]
                # Use the stored node_name as the parameter key.
                if current_node.node_name is not None:
                    kwargs[current_node.node_name] = part
            else:
                # No matching branch found.
                return None

        #If we have reached a node that has a callback, return it along with the kwargs.
        if current_node.callback is not None:
            return current_node.callback, kwargs
        return None

    def __mqtt_sub_callback(self, topic: bytes, msg: bytes):
        print(f"[DEBUG] Received message from {topic}: {msg}")
        if topic is None:
            print("[WARNING] Received message from invalid topic. Ignoring.")
            return

        action = self.__extract_action_path(topic)
        if action is None or len(action) == 0:
            print("[WARNING Received message from invalid topic. Ignoring.")
            return

        if action in self.__action_cb_dict:
            func = self.__action_cb_dict[action].callback
            try:
                func(self, msg)
            except Exception as e:
                print(f"[ERROR] Action callback `{func.__name__}` failed: {e}")
           
            return

        found = self.__find_action_callback(action, msg)
        if found is None:
            print(f"[ERROR] No action callback found for `{action}`")
            return
        func, kwargs = found
        try:
            func(self, msg, **kwargs)
        except Exception as e:
            print(f"[ERROR] Action callback `{func.__name__}` with kwargs `{kwargs}` failed to execute: {e}")

    def __connect(self, last_will: str | None = None, _with_registration: bool = False):
        CONFIG = self.__load_config()
        self.__validate_config(CONFIG)

        try:
            WIFI_SSID = CONFIG["wifi"]["ssid"]
            WIFI_PASSWORD = CONFIG["wifi"]["password"]
            self.__wlan_connect(WIFI_SSID, WIFI_PASSWORD)
        except Exception as e:
            raise Exception(f"[ERROR] wlan connection failed: {e}") from e

        try:
            MQTT_HOST = CONFIG['broker']['host']
            MQTT_PORT = CONFIG['broker']['port']
            self.__mqtt_connect(self.UUID, MQTT_HOST, MQTT_PORT)
        except Exception as e:
            raise Exception(f"[ERROR] MQTT broker connection failed: {e}") from e

        if _with_registration:
            self.__mqtt.publish(self.REGISTRATION_TOPIC,
                                json.dumps(CONFIG["self_id"]), retain=True, qos=1)
            print("[INFO] Registration published")

        #NOTE: CONFIG is not handled as a true property, as it is not expected to change
        # This means that with retain, pushing the config after registration will comply
        # with the spec and remove the need to keep the CONFIG variable in memory
        self.__mqtt.publish(f"{self.BASE_TOPIC}/properties/ssa_hal/config",
                            json.dumps(CONFIG), retain=True, qos=1)
        print("[INFO] Config published")

    def __publish(self, subtopic:str, msg:str, retain: bool = False, qos: int = 0):
        print(f"[DEBUG] Publishing `{msg}` to `{subtopic}`")
        self.__mqtt.publish(f"{self.BASE_TOPIC}/{subtopic}", msg, retain=retain, qos=qos)

        
    #TODO: improve main loop periodicity by taking into account the time taken by message processing
    async def __main_loop(self, _blocking: bool = False):
        """
        Run the main loop of the application
        @param _blocking: If True, the loop will block until a message is received.
        If False, the loop will run in the background and periodically check for incoming messages
        Blocking mode is an not meant for user code and is used as part of the bootstrap process
        to wait fo incoming firmware updates.
        """
        self.create_action_callback("ssa_hal/set/{prop}", __property_update_action)
        self.create_action_callback("ssa_hal/firmware", __fw_update_callback)
        self.__mqtt.set_callback(self.__mqtt_sub_callback)
        self.__mqtt.subscribe(f"{self.BASE_ACTION_TOPIC}/#", qos=1)

        while True:
            if _blocking:
                self.__mqtt.wait_msg()
            else:
                #TODO: Add a way to stop the loop
                #TODO: Allow for configuration of the loop period
                self.__mqtt.check_msg()
                await asyncio.sleep_ms(200)

    def create_property(self, name: str, value: Any):
        """
        Create a property for the device
        @param name: The name of the property
        @param value: The initial value of the property
        """
        if name in self.__properties:
            raise Exception(f"[ERROR] Property `{name}` already exists. Use `set_property` to update it.")
        self.__properties[name] = value

    def get_property(self, name: str) -> Any:
        """
        Get the value of a property
        @param name: The name of the property
        @returns Any: The value of the property
        """
        if name not in self.__properties:
            raise Exception(f"[ERROR] Property `{name}` does not exist. Create it using `create_property` before getting it.")
        return self.__properties[name]

    def set_property(self, name: str, value: Any, retain: bool = False, qos: int = 0):
        """
        Set the value of a property.
        Properties are published to the broker when set, if the value has changed
        @param name: The name of the property
        @param value: The new value of the property
        """
        if name not in self.__properties:
            raise Exception(f"[ERROR] Property `{name}` does not exist. Create it using `create_property` before setting it.")

        prev_value = self.__properties[name]
        if prev_value != value:
            self.__properties[name] = value
            self.__publish(f"properties/{name}", str(value), retain=retain, qos=qos)

    def trigger_event(self, name: str, value: Any, retain: bool = False, qos: int = 0):
        """
        Trigger an event
        Events are published to the broker when triggered
        @param name: The name of the event
        @param value: The value of the event
        """
        self.__publish(f"events/{name}", str(value), retain=retain, qos=qos)

    def create_task(self, task: Callable[[], Awaitable[None]]):
        """
        Register a task to be executed as part of the main loop
        @param task: The task to be executed
        The task should be an async function decorated with @ssa_property_task or @ssa_event_task
        See the ssa.decorators.py documentation for more information
        """
        async def wrapped_task():
            try:
                await task()
            except Exception as e:
                print(f"[WARNING] Task failed: {e}")
            finally:
                if task in self.__tasks:
                    self.__tasks.remove(task)

        self.__tasks.append(asyncio.create_task(wrapped_task()))

    def create_action_callback(self, uri: str, callback_func: Callable[[SSA, str, ...], None]):
        """
        Register a callback function to be executed when an action message is received
        @param action: The name of the action to register the callback for
        @param callback_func: The function to be called when the action message is received The function should take two arguments: the SSA instance and the message
        If the action has URI parameters, the function should take three arguments: the SSA instance, the sub-action and the message

        Usage: 
        URI parameters are defined using curly braces in the action name. For example, an action `foo/{bar}` has a URI parameter `bar`
        Sub-actions are defined using a forward slash in the action name. For example, an action `foo/bar` has a sub-action `bar`
        The first component of an action cannot be a URI parameter (i.e. an action `foo/{bar}` is valid, but an action `{foo}/bar` is not)
        There can be multiple URI parameters in an action name. For example, an action `foo/{bar}/baz/{qux}` has two URI parameters `bar` and `qux`
        The callback function signature should match the URI parameters in the action name. The first 2 arguments are always the SSA instance and the received message

        There is tecnically no limit to the number of URI parameters in an action name, so the limiting factor becomes device memory and processing power when parsing the action name

        example with no URI parameters:
        # For action `foo`
        def callback1(ssa: SSA, msg: str) -> None:
            print(f"Action foo triggered with message: {msg}")

        ssa.register_action_callback("foo", callback)

        example with a sub-action:
        # For action `foo/bar`
        def callback2(ssa: SSA, msg: str) -> None:
            print(f"Action foo/bar triggered with message: {msg}")

        example with URI parameters:
        # For action `foo/{bar}`
        def callback3(ssa: SSA, msg: str, bar: str) -> None:
            print(f"Action foo/{bar}: {msg}")

        example with URI parameters and sub-actions:
        # For actions `foo/{bar}/baz/qux/{quux}`
        def callback4(ssa: SSA, msg: str, bar: str, quux: str) -> None:
            print(f"Action foo/{bar}/baz/qux/{quux}: {msg}")

        example with adjacent URI parameters:
        # For action `foo/{bar}/{baz}`
        def callback5(ssa: SSA, msg: str, bar: str, baz: str) -> None:
            print(f"Action foo/{bar}/{baz}: {msg}")

        Implementation details:
        Internally, actions are stored in a tree-like dictionary structure, where each node is an instance of the ActDictElement class
        The ActDictElement class has three attributes:
        - callback: The callback function to be executed when the action for this node is triggered
        - node_name: The name of the URI parameter for this node, if it exists
        - children: A dictionary of the children of this node, where the key is the name of the child node and the value is the ActDictElement instance for the child node
            
        The resulting dictionary structure for the examples above would be:
        {
            "*": None # Special case for the root node of the tree. This entry does not exist in the dictionary, but is used to represent the root node
            "foo": ActDictElement(callback=callback1, variable="bar", children=dict2)
            "foo/bar": ActDictElement(callback=callback2, variable=None, children=None)
        }

        dict2:
        {
            "*": ActDictElement(callback=callback3, variable="baz", children=dict3)
            "baz": ActDictElement(callback=None, variable=None, children=dict4)
        }

        dict3: { "*": ActDictElement(callback=callback5, variable=None, children=None) }

        dict4: { "qux": ActDictElement(callback=None, variable="quux", children=dict5) }

        dict5: { "*": ActDictElement(callback=callback4, variable=None, children=None) }
        """
        # Case 1: No URI parameters (literal action)
        if "{" not in uri:
            if uri in self.__action_cb_dict:
                raise Exception(f"[ERROR] callback for `{uri}` already exists")
            self.__action_cb_dict[uri] = ActDictElement(callback=callback_func, node_name=None, children={})
            return

        # Split the URI into parts.
        uri_parts = uri.split("/")
        # The first part must be a literal.
        if uri_parts[0].startswith("{"):
            raise Exception(f"[ERROR] URI parameter cannot be the first part of an action name")

        # Process the first literal part.
        first_part = uri_parts[0]
        if first_part not in self.__action_cb_dict:
            self.__action_cb_dict[first_part] = ActDictElement(callback=None, node_name=None, children={})
        current_node = self.__action_cb_dict[first_part]
        current_dict = current_node.children

        # Process each subsequent part.
        for part in uri_parts[1:]:
            if part.startswith("{") and part.endswith("}"):
                # This is a URI parameter.
                var_name = part[1:-1]
                key = "*"
                if key not in current_dict:
                    current_dict[key] = ActDictElement(callback=None, node_name=var_name, children={})
                else:
                    if current_dict[key].node_name is None:
                        current_dict[key].node_name = var_name
                current_node = current_dict[key]
            else:
                # This is a literal segment.
                key = part
                if key not in current_dict:
                    current_dict[key] = ActDictElement(callback=None, node_name=None, children={})
                current_node = current_dict[key]

            # If not at the last segment, prepare for the next level.
            if part != uri_parts[-1]:
                if current_node.children is None:
                    current_node.children = {}
                current_dict = current_node.children

        # At the final node, set the callback.
        if current_node.callback is not None:
            raise Exception(f"[ERROR] callback for `{uri}` already exists")
        current_node.callback = callback_func
