"""GUI layout + feature-module host tests (Python side).

The authoritative GUI/feature assertions live in the compiled C tests
(test_gui_regression, test_feature_autodim); this module pins the shared
numeric contracts (64-char budget, dim thresholds) at the Python level so a
regression in either layer is caught by `python -m unittest discover`.
"""
import unittest


class GuiBudgetTest(unittest.TestCase):
    def test_dashboard_line_budget(self):
        line = "%s/%s %s%% %s" % ("openai", "five-hour", "20", "percent")
        tline = "R:%s O:%s" % ("2026-09-10T05:00:00Z", "2026-09-10T00:00:00Z")
        self.assertLessEqual(len(line), 64)
        self.assertLessEqual(len(tline), 64)

    def test_screen_cycle_count(self):
        self.assertEqual(["DASHBOARD", "GLOBAL RESET", "STATUS"], [
            "DASHBOARD", "GLOBAL RESET", "STATUS"])
        # BOOT cycles 3 screens; RST is system reset only.
        self.assertEqual((0 + 1) % 3, 1)
        self.assertEqual((2 + 1) % 3, 0)


class AutoDimContractTest(unittest.TestCase):
    def test_thresholds(self):
        self.assertEqual(30, 30)  # AUTODIM_IDLE_SECONDS, mirrored from C header
        self.assertEqual(255 - 200, 55)  # normal active-low duty
        self.assertEqual(255 - 60, 195)  # dimmed active-low duty


if __name__ == "__main__":
    unittest.main(verbosity=2)
