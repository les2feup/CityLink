import unittest

# Define the ActDictElement class
class ActDictElement:
    def __init__(self, callback=None, node_name=None, children=None):
        self.callback = callback
        self.node_name = node_name
        self.children = children if children is not None else {}

# Dummy SSA class with the create_action_callback implementation
class DummySSA:
    def __init__(self):
        # The internal dictionary storing actions.
        self.actions = {}

    def _find_dedicated_handler(self, action_uri):
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

    def register_action(self, action_uri: str, handler_func):
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
            raise Exception("[ERROR] URI parameter cannot be the first part of an action name")

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
    # A helper method for testing to inspect the internal dictionary.
    def get_action_dict(self):
        return self.actions


# Unit tests for the create_action_callback functionality
class TestSSAActionCallback(unittest.TestCase):
    def setUp(self):
        self.ssa = DummySSA()

    def test_register_no_parameters(self):
        # Register a literal action (no URI parameters)
        def callback1(ssa, msg):
            pass

        self.ssa.register_action("foo", callback1)
        action_dict = self.ssa.get_action_dict()
        self.assertIn("foo", action_dict)
        self.assertEqual(action_dict["foo"].callback, callback1)
        self.assertEqual(action_dict["foo"].children, {})

        # Attempting to register the same literal action should raise an exception.
        with self.assertRaises(Exception) as context:
            self.ssa.register_action("foo", callback1)
        self.assertIn("callback for `foo` already exists", str(context.exception))

    def test_register_subaction_no_parameters(self):
        # Register a literal sub-action (no URI parameters)
        def callback2(ssa, msg):
            pass

        self.ssa.register_action("foo/bar", callback2)
        action_dict = self.ssa.get_action_dict()
        # In this case, the entire action "foo/bar" is a key in the top-level dictionary.
        self.assertIn("foo/bar", action_dict)
        self.assertEqual(action_dict["foo/bar"].callback, callback2)

    def test_register_uri_parameter(self):
        # Register an action with one URI parameter: foo/{bar}
        def callback3(ssa, msg, bar):
            pass

        self.ssa.register_action("foo/{bar}", callback3)
        action_dict = self.ssa.get_action_dict()
        # The literal "foo" should exist.
        self.assertIn("foo", action_dict)
        foo_node = action_dict["foo"]
        # Under foo_node.children, there should be a key "*" for the parameter.
        self.assertIn("*", foo_node.children)
        bar_node = foo_node.children["*"]
        self.assertEqual(bar_node.node_name, "bar")
        self.assertEqual(bar_node.callback, callback3)

    def test_register_uri_parameter_and_subaction(self):
        # Register an action with a URI parameter and sub-action:
        # foo/{bar}/baz/qux/{quux}
        def callback4(ssa, msg, bar, quux):
            pass

        self.ssa.register_action("foo/{bar}/baz/qux/{quux}", callback4)
        action_dict = self.ssa.get_action_dict()
        self.assertIn("foo", action_dict)
        foo_node = action_dict["foo"]
        self.assertIn("*", foo_node.children)  # parameter {bar}
        bar_node = foo_node.children["*"]
        self.assertIn("baz", bar_node.children)
        baz_node = bar_node.children["baz"]
        self.assertIn("qux", baz_node.children)
        qux_node = baz_node.children["qux"]
        self.assertIn("*", qux_node.children)  # parameter {quux}
        quux_node = qux_node.children["*"]
        self.assertEqual(quux_node.node_name, "quux")
        self.assertEqual(quux_node.callback, callback4)

    def test_register_adjacent_uri_parameters(self):
        # Register an action with adjacent URI parameters: foo/{bar}/{baz}
        def callback5(ssa, msg, bar, baz):
            pass

        self.ssa.register_action("foo/{bar}/{baz}", callback5)
        action_dict = self.ssa.get_action_dict()
        self.assertIn("foo", action_dict)
        foo_node = action_dict["foo"]
        self.assertIn("*", foo_node.children)  # for {bar}
        bar_node = foo_node.children["*"]
        # The next adjacent parameter should be stored under the same special key "*"
        self.assertIn("*", bar_node.children)
        baz_node = bar_node.children["*"]
        self.assertEqual(baz_node.node_name, "baz")
        self.assertEqual(baz_node.callback, callback5)

    def test_error_if_first_part_parameter(self):
        # Attempt to register an action where the first part is a URI parameter.
        def dummy_callback(ssa, msg, foo):
            pass

        with self.assertRaises(Exception) as context:
            self.ssa.register_action("{foo}/bar", dummy_callback)
        self.assertIn("URI parameter cannot be the first part", str(context.exception))

    def test_error_duplicate_registration_parameter(self):
        # Register an action with a parameter, then try to register it again.
        def callback6(ssa, msg, bar):
            pass

        self.ssa.register_action("foo/{bar}", callback6)
        with self.assertRaises(Exception) as context:
            self.ssa.register_action("foo/{bar}", callback6)
        self.assertIn("callback for `foo/{bar}` already exists", str(context.exception))

# Unit tests for the __find_action_callback functionality
class TestFindActionCallback(unittest.TestCase):
    def setUp(self):
        self.ssa = DummySSA()

    def test_parameter_action(self):
        # Register an action with one URI parameter: foo/{bar}
        def callback(ssa, msg, bar):
            return f"bar: {bar}"
        self.ssa.register_action("foo/{bar}", callback)
        result = self.ssa._find_dedicated_handler("foo/1123")
        self.assertIsNotNone(result)
        cb, kwargs = result
        self.assertEqual(cb, callback)
        self.assertEqual(kwargs, {"bar": "1123"})

    def test_parameter_subaction(self):
        # Register an action with a URI parameter and additional literal segments.
        # Example: foo/{bar}/baz/qux/{quux}
        def callback(ssa, msg, bar, quux):
            return f"{bar} and {quux}"
        self.ssa.register_action("foo/{bar}/baz/qux/{quux}", callback)
        result = self.ssa._find_dedicated_handler("foo/123/baz/qux/456")
        self.assertIsNotNone(result)
        cb, kwargs = result
        self.assertEqual(cb, callback)
        self.assertEqual(kwargs, {"bar": "123", "quux": "456"})

    def test_adjacent_parameters(self):
        # Register an action with adjacent URI parameters: foo/{bar}/{baz}
        def callback(ssa, msg, bar, baz):
            return f"{bar} and {baz}"
        self.ssa.register_action("foo/{bar}/{baz}", callback)
        result = self.ssa._find_dedicated_handler("foo/111/222")
        self.assertIsNotNone(result)
        cb, kwargs = result
        self.assertEqual(cb, callback)
        self.assertEqual(kwargs, {"bar": "111", "baz": "222"})

    def test_incomplete_action(self):
        # Register an action that requires more segments and test that an incomplete action returns None.
        def callback(ssa, msg, bar):
            return "complete"
        self.ssa.register_action("foo/{bar}/baz", callback)
        # "foo/1123" is incomplete because the full action is "foo/{bar}/baz"
        result = self.ssa._find_dedicated_handler("foo/1123")
        self.assertIsNone(result)

    def test_nonexistent_action(self):
        # Test that an action that does not exist returns None.
        result = self.ssa._find_dedicated_handler("nonexistent")
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
