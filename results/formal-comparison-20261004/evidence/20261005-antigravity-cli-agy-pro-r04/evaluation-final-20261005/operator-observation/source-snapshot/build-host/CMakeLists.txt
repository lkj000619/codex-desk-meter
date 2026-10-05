cmake_minimum_required(VERSION 3.16)
project(meter_host)

set(IDF_PATH "C:/Espressif/v5.3.2/esp-idf")
include_directories(${IDF_PATH}/components/json/cJSON)
include_directories(../firmware/main)

add_executable(test_meter_parser
    test_meter_parser.cpp
    ../firmware/main/meter_state.c
    ${IDF_PATH}/components/json/cJSON/cJSON.c
)
