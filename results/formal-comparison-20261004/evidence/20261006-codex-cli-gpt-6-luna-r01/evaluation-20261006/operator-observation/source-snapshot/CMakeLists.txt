cmake_minimum_required(VERSION 3.16)

set(VENDOR_ROOT "C:/Espressif/vendor/waveshare-esp32-s3-lcd-3.16/source/ESP32-S3-LCD-3.16-Demo/ESP-IDF/09_FactoryProgram")
set(ENV{IDF_COMPONENT_MANAGER} "0")
set(EXTRA_COMPONENT_DIRS
    "${CMAKE_CURRENT_LIST_DIR}/components/meter_core"
    "${CMAKE_CURRENT_LIST_DIR}/components/idle_dim_policy"
    "${CMAKE_CURRENT_LIST_DIR}/components/vendor_panel_io_additions"
    "${CMAKE_CURRENT_LIST_DIR}/components/vendor_io_expander"
    "${CMAKE_CURRENT_LIST_DIR}/components/vendor_st7701")

include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(codex_desk_meter)
