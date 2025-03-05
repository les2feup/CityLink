import unittest

from ssa._action_handler import ActionHandler

# Dummy SSA class to pass into ActionHandler.
class DummySSA:
    def __init__(self):
        self.tasks = []  # Record of tasks created.

    def create_task(self, handler, payload, **kwargs):
        # For testing, simply record the handler call instead of launching an async task.
        self.tasks.append((handler, payload, kwargs))

# -------------------------------
# Tests for action registration.
# -------------------------------
class TestActionHandlerRegistration(unittest.TestCase):
    def setUp(self):
        self.dummy_ssa = DummySSA()
        self.ah = ActionHandler(self.dummy_ssa)

    def test_register_no_parameters(self):
        # Register a literal action (no URI parameters)
        def callback1(ssa, msg):
            return "callback1"
        self.ah.register_action("foo", callback1)
        # Since there are no URI parameters, the entire action URI is used as the key.
        self.assertIn("foo", self.ah.actions)
        elem = self.ah.actions["foo"]
        self.assertEqual(elem.callback, callback1)
        self.assertEqual(elem.children, {})

        # Registering the same literal action again should raise an exception.
        with self.assertRaises(Exception) as context:
            self.ah.register_action("foo", callback1)
        self.assertIn("callback for `foo` already exists", str(context.exception))

    def test_register_subaction_no_parameters(self):
        # Register a literal sub-action. In this design, if the URI has no parameters,
        # the full URI string is used as a key.
        def callback2(ssa, msg):
            return "callback2"
        self.ah.register_action("foo/bar", callback2)
        self.assertIn("foo/bar", self.ah.actions)
        elem = self.ah.actions["foo/bar"]
        self.assertEqual(elem.callback, callback2)

    def test_register_uri_parameter(self):
        # Register an action with one URI parameter: foo/{bar}
        def callback3(ssa, msg, bar):
            return f"bar: {bar}"
        self.ah.register_action("foo/{bar}", callback3)
        # The first literal segment ("foo") should be registered.
        self.assertIn("foo", self.ah.actions)
        foo_node = self.ah.actions["foo"]
        # Under foo_node.children, a parameter node is stored under the wildcard key "*".
        self.assertIn("*", foo_node.children)
        bar_node = foo_node.children["*"]
        self.assertEqual(bar_node.node_name, "bar")
        self.assertEqual(bar_node.callback, callback3)

    def test_register_uri_parameter_and_subaction(self):
        # Register an action with a URI parameter and literal sub-actions:
        # foo/{bar}/baz/qux/{quux}
        def callback4(ssa, msg, bar, quux):
            return f"{bar} and {quux}"
        self.ah.register_action("foo/{bar}/baz/qux/{quux}", callback4)
        self.assertIn("foo", self.ah.actions)
        foo_node = self.ah.actions["foo"]
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
            return f"{bar} and {baz}"
        self.ah.register_action("foo/{bar}/{baz}", callback5)
        self.assertIn("foo", self.ah.actions)
        foo_node = self.ah.actions["foo"]
        self.assertIn("*", foo_node.children)  # for {bar}
        bar_node = foo_node.children["*"]
        # The adjacent parameter {baz} is stored under "*" in bar_node.children.
        self.assertIn("*", bar_node.children)
        baz_node = bar_node.children["*"]
        self.assertEqual(baz_node.node_name, "baz")
        self.assertEqual(baz_node.callback, callback5)

    def test_error_if_first_part_parameter(self):
        # Attempt to register an action where the first part is a URI parameter.
        def dummy_callback(ssa, msg, foo):
            return "dummy"
        with self.assertRaises(Exception) as context:
            self.ah.register_action("{foo}/bar", dummy_callback)
        self.assertIn("URI parameter cannot be the first part", str(context.exception))

    def test_error_duplicate_registration_parameter(self):
        # Register an action with a parameter, then try to register it again.
        def callback6(ssa, msg, bar):
            return "callback6"
        self.ah.register_action("foo/{bar}", callback6)
        with self.assertRaises(Exception) as context:
            self.ah.register_action("foo/{bar}", callback6)
        self.assertIn("callback for `foo/{bar}` already exists", str(context.exception))

# ----------------------------------------
# Tests for finding a dedicated handler.
# ----------------------------------------
class TestFindDedicatedHandler(unittest.TestCase):
    def setUp(self):
        self.dummy_ssa = DummySSA()
        self.ah = ActionHandler(self.dummy_ssa)

    def test_parameter_action(self):
        # Register an action with one URI parameter: foo/{bar}
        def callback(ssa, msg, bar):
            return f"bar: {bar}"
        self.ah.register_action("foo/{bar}", callback)
        result = self.ah._find_dedicated_handler("foo/1123")
        self.assertIsNotNone(result)
        cb, kwargs = result
        self.assertEqual(cb, callback)
        self.assertEqual(kwargs, {"bar": "1123"})

    def test_parameter_subaction(self):
        # Register an action with a URI parameter and additional literal segments.
        # Example: foo/{bar}/baz/qux/{quux}
        def callback(ssa, msg, bar, quux):
            return f"{bar} and {quux}"
        self.ah.register_action("foo/{bar}/baz/qux/{quux}", callback)
        result = self.ah._find_dedicated_handler("foo/123/baz/qux/456")
        self.assertIsNotNone(result)
        cb, kwargs = result
        self.assertEqual(cb, callback)
        self.assertEqual(kwargs, {"bar": "123", "quux": "456"})

    def test_adjacent_parameters(self):
        # Register an action with adjacent URI parameters: foo/{bar}/{baz}
        def callback(ssa, msg, bar, baz):
            return f"{bar} and {baz}"
        self.ah.register_action("foo/{bar}/{baz}", callback)
        result = self.ah._find_dedicated_handler("foo/111/222")
        self.assertIsNotNone(result)
        cb, kwargs = result
        self.assertEqual(cb, callback)
        self.assertEqual(kwargs, {"bar": "111", "baz": "222"})

    def test_incomplete_action(self):
        # Register an action that requires more segments.
        def callback(ssa, msg, bar):
            return "complete"
        self.ah.register_action("foo/{bar}/baz", callback)
        # "foo/1123" is incomplete because the full action is "foo/{bar}/baz"
        result = self.ah._find_dedicated_handler("foo/1123")
        self.assertIsNone(result)

    def test_nonexistent_action(self):
        # Test that an action that does not exist returns None.
        result = self.ah._find_dedicated_handler("nonexistent")
        self.assertIsNone(result)

# ----------------------------------------
# Tests for global handler invocation.
# ----------------------------------------
class TestGlobalHandler(unittest.TestCase):
    def setUp(self):
        self.dummy_ssa = DummySSA()
        self.ah = ActionHandler(self.dummy_ssa)

    def test_global_handler_literal(self):
        # Test that a literal action is invoked via global_handler.
        def callback(ssa, msg):
            return "global literal"
        self.ah.register_action("foo", callback)
        self.ah.global_handler("foo", "payload1")
        # For literal actions, the key is the full URI.
        self.assertEqual(len(self.dummy_ssa.tasks), 1)
        task = self.dummy_ssa.tasks[0]
        self.assertEqual(task[0], callback)
        self.assertEqual(task[1], "payload1")
        self.assertEqual(task[2], {})  # No extra kwargs

    def test_global_handler_parameter(self):
        # Test that an action with a URI parameter is invoked correctly.
        def callback(ssa, msg, bar):
            return f"global parameter {bar}"
        self.ah.register_action("foo/{bar}", callback)
        self.ah.global_handler("foo/789", "payload2")
        self.assertEqual(len(self.dummy_ssa.tasks), 1)
        task = self.dummy_ssa.tasks[0]
        self.assertEqual(task[0], callback)
        self.assertEqual(task[1], "payload2")
        self.assertEqual(task[2], {"bar": "789"})

    def test_global_handler_nonexistent(self):
        # Test that invoking a nonexistent action prints an error.
        # For testing purposes, we can capture output if needed,
        # but here we'll simply check that no task was created.
        self.ah.global_handler("nonexistent", "payload3")
        self.assertEqual(len(self.dummy_ssa.tasks), 0)

if __name__ == '__main__':
    unittest.main()
