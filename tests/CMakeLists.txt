cmake_minimum_required(VERSION 3.20)
project(cdm_receiver_tests C)

set(CDM_IDF_ROOT "C:/Espressif/v5.3.2/esp-idf" CACHE PATH "Pinned ESP-IDF tree")
add_executable(test_receiver_core
    test_receiver_core.c
    ../main/cdm_receiver.c
    ${CDM_IDF_ROOT}/components/json/cJSON/cJSON.c)
target_include_directories(test_receiver_core PRIVATE
    ../main
    ${CDM_IDF_ROOT}/components/json/cJSON)
target_compile_features(test_receiver_core PRIVATE c_std_11)
if(MSVC)
    target_compile_options(test_receiver_core PRIVATE /W4)
else()
    target_compile_options(test_receiver_core PRIVATE -Wall -Wextra -Werror -Wframe-larger-than=4096)
endif()
enable_testing()
add_test(NAME receiver_core COMMAND test_receiver_core
    ../tests/fixtures/default_repository_frame.jsonl)

add_executable(test_main_loop test_main_loop.c ../main/cdm_receiver.c
    ${CDM_IDF_ROOT}/components/json/cJSON/cJSON.c)
target_include_directories(test_main_loop PRIVATE idf_stubs ../main
    ${CDM_IDF_ROOT}/components/json/cJSON)
target_compile_features(test_main_loop PRIVATE c_std_11)
add_test(NAME native_usb_to_display COMMAND test_main_loop usb)
add_test(NAME boot_render_latency_and_hold COMMAND test_main_loop boot)
