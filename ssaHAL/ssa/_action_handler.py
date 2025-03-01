
class ActDictElement():
    def __init__(self, callback = None, node_name = None, children = {}):
        self.callback = callback
        self.node_name = node_name
        self.children = children

class ActionHandler():
    def __init__(self, ssa_instance):
        self._ssa = ssa_instance
        self.actions = {}

    def _find_dedicated_handler(self, uri, msg):
        """Walks the action tree using the given action uri string.
        Returns a tuple (callback_function, kwargs) if a callback is found,
        or None if no callback matches the action.

        The kwargs dictionary maps URI parameter names to their corresponding
        values.

        For example, if the action "foo/{bar}/baz" is called with
        "foo/1123/baz", then kwargs will be {"bar": "1123"}.
        """
        parts = action.split("/")
        # The first part must be a literal.
        if parts[0] not in self.actions:
            return None

        current_node = self.actions[parts[0]]
        kwargs = {}  # dictionary to hold parameter values
                     # mapped by their node_name

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

        # If we have reached a node that has a callback,
        # return it along with the kwargs.
        if current_node.callback is not None:
            return current_node.callback, kwargs

        return None

    def global_handler(self, uri, payload):
        """Global action handler for all actions.
        This handler is called when an action is invoked by the WoT servient.
        @param uri: The URI of the action (relative to the base action URI)
        @param payload: The payload of the action.
        """

        if topic is None:
            print("[WARNING] Received message from invalid topic. Ignoring.")
            return

        if uri is None or len(uri) == 0:
            print("[WARNING] Received message from invalid topic. Ignoring.")
            return

        # Check if the uri matches a top-level action
        if uri in self.actions:
            handler = self.actions[uri].callback
            try:
                handler(self._ssa, msg) # Invoke the action handler
            except Exception as e:
                print(f"[ERROR] Action callback `{handler.__name__}` \
                        failed to execute: {e}")
            return

        found = self._find_dedicated_handler(uri, msg)
        if found is None:
            print(f"[ERROR] No action handler found for `{uri}`")
            return
        handler, kwargs = found
        try:
            handler(self._ssa, msg, **kwargs)
        except Exception as e:
            func_name = handler.__name__ if hasattr(handler, "__name__") \
                    else "unknown"
            print(f"[ERROR] Action callback `{func_name}` with kwargs \
                    `{kwargs}` failed to execute: {e}")

    def register_action(self, action_uri, handler_func):
        """Register a callback function to be executed when an action message
        is received
        @param action_uri: The name of the action to register the callback for
        @param handler_func: The function to be called when the action message
        is received.

        Usage:
        URI parameters are defined using curly braces in the action name.
        For example, an action `foo/{bar}` has a URI parameter `bar`

        Sub-actions are defined using a forward slash in the action name.
        For example, an action `foo/bar` has a sub-action `bar`

        The first component of an action cannot be a URI parameter
        (i.e. an action `foo/{bar}` is valid, but an action `{foo}/bar` is not)

        There can be multiple URI parameters in an action name.
        For example, an action `foo/{bar}/baz/{qux}` has two URI parameters
        `bar` and `qux`

        The handler function signature should match the URI parameters in the
        action name. The first 2 arguments are always the SSA instance and the
        received message.

        There is tecnically no limit to the number of URI parameters in an
        action name, so the limiting factor becomes device memory and
        processing power when parsing the action name

        example with no URI parameters:
        # For action `foo`
        def callback1(ssa: SSA, msg: str) -> None:
            print(f"Action foo triggered with message: {msg}")

        ssa.create_action_callback("foo", callback1)

        example with a sub-action:
        # For action `foo/bar`
        def callback2(ssa: SSA, msg: str) -> None:
            print(f"Action foo/bar triggered with message: {msg}")

        ssa.create_action_callback("foo/bar", callback2)

        example with URI parameters:
        # For action `foo/{bar}`
        def callback3(ssa: SSA, msg: str, bar: str) -> None:
            print(f"Action foo/{bar}: {msg}")

        ssa.create_action_callback("foo/{bar}", callback3)

        example with URI parameters and sub-actions:
        # For actions `foo/{bar}/baz/qux/{quux}`
        def callback4(ssa: SSA, msg: str, bar: str, quux: str) -> None:
            print(f"Action foo/{bar}/baz/qux/{quux}: {msg}")

        ssa.create_action_callback("foo/{bar}/baz/qux/{quux}", callback4)

        example with adjacent URI parameters:
        # For action `foo/{bar}/{baz}`
        def callback5(ssa: SSA, msg: str, bar: str, baz: str) -> None:
            print(f"Action foo/{bar}/{baz}: {msg}")

        ssa.create_action_callback("foo/{bar}/{baz}", callback5)

        Implementation details:
        Internally, actions are stored in a tree-like dictionary structure,
        where each node is an instance of the ActDictElement class

        The ActDictElement class has three attributes:
        - callback: The callback function to be executed when the action for
        this node is triggered
        - node_name: The name of the URI parameter for this node, if it exists
        - children: A dictionary of the children of this node, where the key is
        the name of the child node and the value is the ActDictElement instance
        for the child node

        The resulting dictionary structure for the examples above would be:
        root: {
                "foo": ActDictElement(callback=callback1,
                                  node_name="bar",
                                  children=dict2)
                "foo/bar": ActDictElement(callback=callback2,
                                      node_name=None,
                                      children={})
                }

        dict2: {
                "*": ActDictElement(callback=callback3,
                                node_name="baz",
                                children=dict3)
                "baz": ActDictElement(callback=None,
                                  node_name=None,
                                  children=dict4)
                }

        dict3: {
                "*": ActDictElement(callback=callback5,
                                     node_name=None,
                                     children={})
                }

        dict4: {
                "qux": ActDictElement(callback=None,
                                       node_name="quux",
                                       children=dict5)
                }

        dict5: {
                "*": ActDictElement(callback=callback4,
                                     node_name=None,
                                     children={})
                }
        """
        # Case 1: No URI parameters (literal action)
        if "{" not in uri:
            if uri in self.actions:
                raise Exception(f"[ERROR] callback for `{uri}` already exists")
            self.actions[uri] = ActDictElement(callback=callback_func)
            return

        # Split the URI into parts.
        uri_parts = uri.split("/")
        # The first part must be a literal.
        if uri_parts[0].startswith("{"):
            raise Exception("[ERROR] URI parameter cannot be the first part \
                    of an action name")

        # Process the first literal part.
        first_part = uri_parts[0]
        if first_part not in self.actions:
            self.actions[first_part] = ActDictElement()
        current_node = self.actions[first_part]
        current_dict = current_node.children

        # Process each subsequent part.
        for part in uri_parts[1:]:
            if part.startswith("{") and part.endswith("}"):
                # This is a URI parameter.
                var_name = part[1:-1]
                key = "*"
                if key not in current_dict:
                    current_dict[key] = ActDictElement(node_name=var_name)
                else:
                    if current_dict[key].node_name is None:
                        current_dict[key].node_name = var_name
                current_node = current_dict[key]
            else:
                # This is a literal segment.
                key = part
                if key not in current_dict:
                    current_dict[key] = ActDictElement()
                current_node = current_dict[key]

            # If not at the last segment, prepare for the next level.
            if part != uri_parts[-1]:
                current_dict = current_node.children

        # At the final node, set the callback.
        if current_node.callback is not None:
            raise Exception(f"[ERROR] callback for `{uri}` already exists")
        current_node.callback = callback_func

def firmware_update(_ssa, update_str):
    print(f"[INFO] Firmware update received with size {len(update_str)}")
    update = json.loads(update_str)


    binary = a2b_base64(update["base64"])
    expected_crc = int(update["crc32"], 16)
    bin_crc = crc32(binary)

    if bin_crc != expected_crc:
        print(f"[ERROR] CRC32 mismatch: expected:{hex(expected_crc)},
              got {hex(bin_crc)} Firmware update failed.")
        return

    if "user" not in os.listdir():
        os.mkdir("user")

    print("[INFO] Writing firmware to device")
    with open("user/app.py", "w") as f:
        f.write(binary.decode("utf-8"))

    print("[INFO] Firmware write complete. Restarting device.")
    from machine import soft_reset
    soft_reset()
