# Compile and Link Evidence

The host adapter uses the exact `meter_state.c` and `meter_state.h` files used by the actual firmware.
It compiles them directly into `test_meter_parser.exe` along with `test_meter_parser.cpp` which acts as the normalizer mock and driver.
This verifies that the state tracking logic used in the firmware correctly handles stale states, error transitions, and cache merging as expected.
