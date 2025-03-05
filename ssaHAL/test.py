import unittest
import ssa_test.stubs as stubs

stubs.init_all_stubs()

from ssa_test.dict_diff_test import TestDictDiffIterativeFull
from ssa_test.action_cb_test import TestActionHandlerRegistration, TestFindDedicatedHandler, TestGlobalHandler

if __name__ == "__main__":
    unittest.main()
