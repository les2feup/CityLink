import unittest
from ssa._utils import iterative_dict_diff

class TestDictDiffIterativeFull(unittest.TestCase):
    def test_no_changes(self):
        old = {"led_1": {"color": "0xff00ff", "brightness": 100}}
        new = {"led_1": {"color": "0xff00ff", "brightness": 100}}
        expected = {}
        self.assertEqual(iterative_dict_diff(old, new), expected)

    def test_top_level_change(self):
        old = {"led_1": {"color": "0xff00ff", "brightness": 100}}
        new = {"led_1": {"color": "0xff0000", "brightness": 100}}
        expected = {"led_1": {"color": "0xff0000"}}
        self.assertEqual(iterative_dict_diff(old, new), expected)

    def test_add_new_key(self):
        old = {"led_1": {"color": "0xff00ff", "brightness": 100}}
        new = {"led_1": {"color": "0xff00ff", "brightness": 100, "is_on": True}}
        expected = {"led_1": {"is_on": True}}
        self.assertEqual(iterative_dict_diff(old, new), expected)
    
    def test_nested_change(self):
        old = {
            "device": {
                "led_1": {"color": "0xff00ff", "brightness": 100},
                "led_2": {"color": "0xffffff", "brightness": 100}
            }
        }
        new = {
            "device": {
                "led_1": {"color": "0xff0000", "brightness": 100},
                "led_2": {"color": "0xffffff", "brightness": 100}
            }
        }
        expected = {"device": {"led_1": {"color": "0xff0000"}}}
        self.assertEqual(iterative_dict_diff(old, new), expected)

    def test_deeply_nested(self):
        # Test a structure with multiple levels of nesting.
        old = {
            "system": {
                "modules": {
                    "module1": {
                        "settings": {
                            "option1": True,
                            "option2": False
                        }
                    },
                    "module2": {
                        "settings": {
                            "option1": 10,
                            "option2": 20
                        }
                    }
                }
            }
        }
        new = {
            "system": {
                "modules": {
                    "module1": {
                        "settings": {
                            "option1": False,   # changed from True to False
                            "option2": False
                        }
                    },
                    "module2": {
                        "settings": {
                            "option1": 10,
                            "option2": 30      # changed from 20 to 30
                        }
                    }
                }
            }
        }
        expected = {
            "system": {
                "modules": {
                    "module1": {
                        "settings": {"option1": False}
                    },
                    "module2": {
                        "settings": {"option2": 30}
                    }
                }
            }
        }
        self.assertEqual(iterative_dict_diff(old, new), expected)
    
    def test_key_not_in_new(self):
        # This test ensures that keys removed in new aren't reflected in the diff,
        # because our algorithm is designed to capture only additions or modifications.
        old = {"led_1": {"color": "0xff00ff", "brightness": 100}}
        new = {}  # led_1 removed from new state
        expected = {}
        self.assertEqual(iterative_dict_diff(old, new), expected)
    
    def test_mixed_changes(self):
        # Test with a mix of unchanged, modified, and added values.
        old = {
            "led_1": {"color": "0xff00ff", "brightness": 100},
            "led_2": {"color": "0xffffff", "brightness": 100},
            "led_3": {"color": "0x0000ff", "brightness": 50}
        }
        new = {
            "led_1": {"color": "0xff00ff", "brightness": 100},  # no change
            "led_2": {"color": "0xff00ff", "brightness": 100},  # color changed
            "led_3": {"color": "0x0000ff", "brightness": 60}     # brightness changed
        }
        expected = {
            "led_2": {"color": "0xff00ff"},
            "led_3": {"brightness": 60}
        }
        self.assertEqual(iterative_dict_diff(old, new), expected)

if __name__ == "__main__":
    unittest.main()
