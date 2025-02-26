import os
import json
import asyncio

from time import sleep
from network import WLAN, STA_IF
from umqtt.simple import MQTTClient
from typing import Any, Dict, List, Tuple, Callable, Awaitable

def __singleton(cls):
    instance = None
    def getinstance(*args, **kwargs):
        nonlocal instance
        if instance is None:
            print("[DEBUG] SSA instance created")
            instance = cls(*args, **kwargs)
        return instance
    return getinstance

def __fw_update_callback(_ssa: SSA, update_str: str):
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

# Recursive type definition for complex action callbacks
type action_callback = Callable[[SSA, ], None]
type acb_dict = Dict[str, 'acb_dict' | Tuple[List[str], action_callback] | action_callback] 

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
        self.__action_cb_dict: acb_dict = {}

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

    def __extract_action_path(self, topic: str) -> str:
        topic = topic.decode("utf-8")
        if topic.startswith(self.BASE_ACTION_TOPIC):
            return topic[len(self.BASE_ACTION_TOPIC) + 1:] # +1 to remove the trailing '/'
        return None

    def __internal_action_handler(self, action: str, msg: str):
        if action == "firmware":
            __fw_update_callback(msg)
            return

        if action.startswith("set/") and action[len("set/"):] in self.__properties:
            self.set_property(action[len("set/"):], msg)
            return
        
        print(f"[WARNING] Received trigger for unknown internal action: {action}")

    def __handle_composite_action(self, action: str | None, msg: str):
        if action is None:
            print("[WARNING] Received message from invalid topic. Ignoring.")
            return

        action_base = action[:action.find("/")]
        if action_base in self.__action_cb_dict:
            cb_dict_value = self.__action_cb_dict[action_base]
            if cb_dict_value.isinstance(dict):
                self.__handle_composite_action(action[action.find("/") + 1:], msg)
                return

            if cb_dict_value.isinstance(tuple):
                remaining_parts = action[action.find("/") + 1:].split("/")
                if len(remaining_parts) != len(cb_dict_value[0]):
                    raise Exception(f"[ERROR] Action {action_base} expected {len(cb_dict_value[0])} parts, got {len(remaining_parts)}")
                try:
                    kwarg_keys = cb_dict_value[0]
                    kwarg_values = remaining_parts
                    kwargs = dict(zip(kwarg_keys, kwarg_values))
                    # signature of the callback function should be such that the remaining parts are mapped to the kwargs in the list
                    func = cb_dict_value[1]
                    func(self, msg, **kwargs)
                except Exception as e:
                    print(f"[Error] action callback {cb_dict_value[1].__name__} failed to execute with kwargs {kwargs}: {e}")

            try:
                cb_dict_value(self, msg)
            except Exception as e:
                print(f"[Error] action callback {cb_dict_value.__name__} failed to execute: {e}")

        else:
            raise Exception(f"[ERROR] Action {action_base} not found in action callback dictionary")

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
            try:
                print(f"[DEBUG] Executing action callback for {action}")
                self.__action_cb_dict[action](self, msg.decode("utf-8"))
            except Exception as e:
                print(f"[WARNING] action callback {self.__action_cb_dict[action].__name__} failed to execute: {e}")
            finally:
                return

        action_parts = action.split("/")
        if len(action_parts) > self.MAX_ACTION_DEPTH:
            print(f"[WARNING] Action depth exceeded. Ignoring message.")
            return

        try:
            self.__handle_composite_action(action , msg)
        except Exception as e:
            print(f"[WARNING] Error handling action {action}: {e}")

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
        """! Run the main loop of the application
            @param _blocking: If True, the loop will block until a message is received.
                              If False, the loop will run in the background and periodically check for incoming messages

                              Blocking mode is an not meant for user code and is used as part of the bootstrap process
                              to wait fo incoming firmware updates.
        """
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
        """! Create a property for the device
            @param name: The name of the property
            @param value: The initial value of the property
        """
        if name in self.__properties:
            raise Exception(f"[ERROR] Property `{name}` already exists. Use `set_property` to update it.")
        self.__properties[name] = value

    def get_property(self, name: str) -> Any:
        """! Get the value of a property
            @param name: The name of the property
            @returns Any: The value of the property
        """
        if name not in self.__properties:
            raise Exception(f"[ERROR] Property `{name}` does not exist. Create it using `create_property` before getting it.")
        return self.__properties[name]

    def set_property(self, name: str, value: Any, retain: bool = False, qos: int = 0):
        """! Set the value of a property.
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
        """! Trigger an event
            Events are published to the broker when triggered
            @param name: The name of the event
            @param value: The value of the event
        """
        self.__publish(f"events/{name}", str(value), retain=retain, qos=qos)

    def create_task(self, task: Callable[[], Awaitable[None]]):
        """! Register a task to be executed as part of the main loop
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

    def create_action_callback(self, uri: str, callback_func: action_callback):
        """! Register a callback function to be executed when an action message is received
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
            Internally the action names, variables and callbacks are stored in a recursive dictionary structure
            The dictionary is structured such that the keys are the action names.
            The there are no URI parameters in an action name, the entired action name is used as a key in the dictionary.
            If there are URI parameters in an action name, the longest common prefix of the action name is used as a key in the dictionary 
            and the remaining parts are stored as a tuple of the variable names and a dictionary of the next parts

            The resulting dictionary structure for the examples above would be:
            {
                "": [None, [None, None]] # This is the root of the dictionary and is not used
                "foo": [callback1, 
                            ["bar", 
                                {
                                    "": [callback3,
                                            [baz, {
                                                "": [callback5, [None, None]]
                                                }
                                             ]
                                         ],
                                    "baz/qux": [callback4, [None, None]]
                                }
                            ]
                        ]
                "foo/bar":  [callback2, [None, None]],
            }
        """
        if uri in self.__action_cb_dict:
            raise Exception(f"[ERROR] callback for `{uri}` already exists")

        if uri.find("{") == -1: # no URI parameters
            if uri not in self.__action_cb_dict:
                self.__action_cb_dict[uri] = [callback_func, [None, None]]
            else:
                self.__action_cb_dict[uri][0] = callback_func
            return

        parts = uri.split("/")
        root = parts[0]
        if root.find("{") != -1:
            raise Exception(f"[ERROR] Invalid action name: {uri}")

        if root not in self.__action_cb_dict:
            self.__action_cb_dict[root] = [None, [None, None]]

        # TODO: Implement recursive dictionary insertion
        return
