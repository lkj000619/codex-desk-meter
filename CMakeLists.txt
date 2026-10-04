cmake_minimum_required(VERSION 3.16)

if(DEFINED CMAKE_TOOLCHAIN_FILE OR DEFINED IDF_TARGET OR DEFINED ENV{IDF_TARGET})
    # ESP-IDF Target Build
    include($ENV{IDF_PATH}/tools/cmake/project.cmake)
    project(meter_esp32s3)
else()
    # Host Target Build
    project(meter_host C CXX)
    enable_testing()

    set(METER_CORE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/components/meter_core")
    set(CJSON_DIR "C:/Espressif/v5.3.2/esp-idf/components/json/cJSON")

    include_directories(
        "${METER_CORE_DIR}/include"
        "${CJSON_DIR}"
    )

    add_library(meter_core STATIC
        "${METER_CORE_DIR}/src/meter_crc.c"
        "${METER_CORE_DIR}/src/meter_parser.c"
        "${METER_CORE_DIR}/src/meter_state.c"
        "${METER_CORE_DIR}/src/feature_imu.c"
        "${METER_CORE_DIR}/src/meter_gui.c"
        "${CJSON_DIR}/cJSON.c"
    )

    # test_meter_parser
    add_executable(test_meter_parser tests/test_meter_parser.c)
    target_link_libraries(test_meter_parser PRIVATE meter_core)
    add_test(NAME test_meter_parser COMMAND test_meter_parser)

    # test_meter_state
    add_executable(test_meter_state tests/test_meter_state.c)
    target_link_libraries(test_meter_state PRIVATE meter_core)
    add_test(NAME test_meter_state COMMAND test_meter_state)

    # test_feature_imu
    add_executable(test_feature_imu tests/test_feature_imu.c)
    target_link_libraries(test_feature_imu PRIVATE meter_core)
    add_test(NAME test_feature_imu COMMAND test_feature_imu)

    # test_gui_regression
    add_executable(test_gui_regression tests/test_gui_regression.c)
    target_link_libraries(test_gui_regression PRIVATE meter_core)
    add_test(NAME test_gui_regression COMMAND test_gui_regression)

    # meter_legacy_adapter
    add_executable(meter_legacy_adapter tests/meter_legacy_adapter.c)
    target_link_libraries(meter_legacy_adapter PRIVATE meter_core)

    # meter-test aggregate target
    add_custom_target(meter-test
        COMMAND ${CMAKE_CTEST_COMMAND} --output-on-failure
        DEPENDS test_meter_parser test_meter_state test_feature_imu test_gui_regression
    )
endif()
