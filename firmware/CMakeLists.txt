cmake_minimum_required(VERSION 3.16)
set(VENDOR_COMPONENTS "C:/Espressif/vendor/waveshare-esp32-s3-lcd-3.16/source/ESP32-S3-LCD-3.16-Demo/ESP-IDF/09_FactoryProgram/managed_components")
set(EXTRA_COMPONENT_DIRS
    "${VENDOR_COMPONENTS}/espressif__cmake_utilities"
    "${VENDOR_COMPONENTS}/espressif__esp_io_expander"
    "${VENDOR_COMPONENTS}/espressif__esp_lcd_panel_io_additions"
    "${VENDOR_COMPONENTS}/espressif__esp_lcd_st7701")
include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(codex_desk_meter)
