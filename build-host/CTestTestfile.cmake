# CMake generated Testfile for 
# Source directory: C:/meter-runs-20261005/20261005-codex-cli-gpt-6-sol-r01/checkout/host
# Build directory: C:/meter-runs-20261005/20261005-codex-cli-gpt-6-sol-r01/checkout/build-host
# 
# This file includes the relevant testing commands required for 
# testing this directory and lists subdirectories to be tested as well.
add_test(receiver_state_and_crc "C:/meter-runs-20261005/20261005-codex-cli-gpt-6-sol-r01/checkout/build-host/receiver_test.exe")
set_tests_properties(receiver_state_and_crc PROPERTIES  _BACKTRACE_TRIPLES "C:/meter-runs-20261005/20261005-codex-cli-gpt-6-sol-r01/checkout/host/CMakeLists.txt;13;add_test;C:/meter-runs-20261005/20261005-codex-cli-gpt-6-sol-r01/checkout/host/CMakeLists.txt;0;")
add_test(python_frame_to_firmware_receiver "C:/Espressif/user-tools/python_env/idf5.3_py3.11_env/Scripts/python.exe" "C:/meter-runs-20261005/20261005-codex-cli-gpt-6-sol-r01/checkout/host/../tests/test_pipeline.py" "C:/meter-runs-20261005/20261005-codex-cli-gpt-6-sol-r01/checkout/build-host/receiver_cli.exe")
set_tests_properties(python_frame_to_firmware_receiver PROPERTIES  _BACKTRACE_TRIPLES "C:/meter-runs-20261005/20261005-codex-cli-gpt-6-sol-r01/checkout/host/CMakeLists.txt;20;add_test;C:/meter-runs-20261005/20261005-codex-cli-gpt-6-sol-r01/checkout/host/CMakeLists.txt;0;")
add_test(idle_backlight_feature "C:/meter-runs-20261005/20261005-codex-cli-gpt-6-sol-r01/checkout/build-host/feature_test.exe")
set_tests_properties(idle_backlight_feature PROPERTIES  _BACKTRACE_TRIPLES "C:/meter-runs-20261005/20261005-codex-cli-gpt-6-sol-r01/checkout/host/CMakeLists.txt;23;add_test;C:/meter-runs-20261005/20261005-codex-cli-gpt-6-sol-r01/checkout/host/CMakeLists.txt;0;")
