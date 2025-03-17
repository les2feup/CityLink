"""
Test runner for the ssa_test package.

The tests are meant to be ran using CPython on the development machine 
as micropython does not provide the unittest module.

Missing dependencies and micropython-specific modules are stubbed out
under the ssa_test.stubs module. The stubs are initialized before the
the tests are imported and ran.
"""

import unittest
import ssa_test.stubs as stubs

stubs.init_all_stubs()

from ssa_test.dict_diff_test import TestDictDiffIterativeFull
from ssa_test.action_cb_test import (
    TestActionHandlerRegistration,
    TestFindDedicatedHandler,
    TestGlobalHandler,
)

__all__ = [
    "TestDictDiffIterativeFull",
    "TestActionHandlerRegistration",
    "TestFindDedicatedHandler",
    "TestGlobalHandler",
]

if __name__ == "__main__":
    unittest.main()
