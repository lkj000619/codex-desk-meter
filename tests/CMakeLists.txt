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
    target_compile_options(test_receiver_core PRIVATE -Wall -Wextra -Werror)
endif()
enable_testing()
add_test(NAME receiver_core COMMAND test_receiver_core)
