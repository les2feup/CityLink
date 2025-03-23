class ActDictElement:
    def __init__(self, callback=None, node_name=None, children=None):
        """
        Initialize an ActDictElement instance.

        Args:
            callback: Optional function called when the action associated with this node is triggered.
            node_name: Optional string representing a URI parameter for this node.
            children: Optional dictionary mapping child names to ActDictElement instances.
        """
        self.callback = callback
        self.node_name = node_name
        self.children = children if children is not None else {}


class ActionHandler:
    def __init__(self, task_launcher):
        """
        Initializes the ActionHandler with the provided task launcher.

        Stores the task launcher for scheduling action callbacks and sets up an empty
        registry for managing action handlers.

        Args:
            task_launcher: An object used to launch or schedule action callbacks.
        """
        self._launcher = task_launcher
        self.actions = {}

    def _find_dedicated_handler(self, action_uri):
        """
        Traverse the action tree to locate a callback matching the given action URI.

        This method splits the URI into segments and walks through the
        hierarchical action tree stored in self.actions. It first evaluates
        literal matches before considering parameterized segments using a
        wildcard key ("*").

        For parameterized segments, the corresponding URI value is stored in a
        dictionary under the node's parameter name. If a node with a valid
        callback is reached, the method returns the callback along with the
        extracted parameters.

        For example, matching "foo/1123/baz" against a route "foo/{bar}/baz"
        produces kwargs {"bar": "1123"}.

        Args:
            action_uri: A string representing the action URI to resolve.

        Returns:
            A tuple (callback_function, kwargs) if a matching callback is found, or None otherwise.
        """
        parts = action_uri.split("/")
        # The first part must be a literal.
        if parts[0] not in self.actions:
            return None

        current_node = self.actions[parts[0]]
        kwargs = {}  # dictionary to hold parameter values
        # mapped by their node_name

        for part in parts[1:]:
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

    def global_handler(self, action_uri, action_input):
        """
        Handles global action invocations by dispatching to the appropriate callback.

        This method routes an action based on its URI by first checking for a top-level
        registered callback. If a match is not found, it searches the action tree for a
        dedicated handler that supports parameterized URIs. If the action URI is invalid
        or no suitable handler exists, a warning or error is logged. Any exceptions raised
        during callback execution are caught and logged.

        Args:
            action_uri: The action's URI relative to the base action URI.
            action_input: The payload data associated with the action invocation.
        """

        if action_uri is None or len(action_uri) == 0:
            print("[WARNING] Received message from invalid topic. Ignoring.")
            return

        # Check if the uri matches a top-level action
        if action_uri in self.actions:
            handler = self.actions[action_uri].callback
            try:
                print(f"[DEBUG] Invoking action handler `{handler.__name__}`")
                self._launcher(handler, action_input)  # Invoke the action handler
                print(f"[DEBUG] Action task launched, exiting global_handler callback`")
            except Exception as e:
                print(f"[ERROR] Action task `{handler.__name__}` failed to launch: {e}")
            return

        found = self._find_dedicated_handler(action_uri)
        if found is None:
            print(f"[ERROR] No action handler found for `{action_uri}`")
            return
        handler, kwargs = found
        try:
            print(
                f"[DEBUG] Invoking action handler `{handler.__name__}` with kwargs `{kwargs}`"
            )
            self._launcher(handler, action_input, **kwargs)  # Invoke the action handler
            print(f"[DEBUG] Action task launched, exiting global_handler callback`")
        except Exception as e:
            func_name = handler.__name__ if hasattr(handler, "__name__") else "unknown"
            print(
                f"[ERROR] Action task `{func_name}` with kwargs `{kwargs}` failed to launch: {e}"
            )

    def register_action(self, action_uri, handler_func):
        """
        Register a callback for a given action URI.

        The action URI may be a literal string or a pattern that includes parameterized segments
        (enclosed in curly braces) and sub-actions (separated by slashes). The first segment
        must be literal. When the action is triggered, the callback will be invoked with the
        action input as its first argument and any extracted URI parameters as keyword arguments.

        Raises:
            Exception: If the action URI is invalid or a callback for the URI already exists.

        Args:
            action_uri: A string representing the action URI to register.
            handler_func: A function to be executed when the action is triggered.
        """
        # Case 1: No URI parameters (literal action)
        if "{" not in action_uri:
            if action_uri in self.actions:
                raise Exception(f"[ERROR] callback for `{action_uri}` already exists")
            self.actions[action_uri] = ActDictElement(callback=handler_func)
            return

        # Split the URI into parts.
        uri_parts = action_uri.split("/")
        # The first part must be a literal.
        if uri_parts[0].startswith("{"):
            raise Exception(
                "[ERROR] URI parameter cannot be the first part of an action name"
            )

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
            raise Exception(f"[ERROR] callback for `{action_uri}` already exists")
        current_node.callback = handler_func
