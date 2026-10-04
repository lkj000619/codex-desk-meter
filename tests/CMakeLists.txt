cmake_minimum_required(VERSION 3.16)
project(cdm_meter_host C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
enable_testing()

set(METER_CORE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../firmware/components/meter_core")
set(GUI_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../firmware/components/gui")
set(FEATURE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../firmware/components/feature_auto_dim")
set(INPUT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../firmware/components/bsp_input")

add_library(meter_core_host STATIC
  "${METER_CORE_DIR}/meter_crc32.c"
  "${METER_CORE_DIR}/meter_parser.c"
  "${METER_CORE_DIR}/meter_state.c"
  "${METER_CORE_DIR}/meter_validate.c"
)
target_include_directories(meter_core_host PUBLIC "${METER_CORE_DIR}/include")

add_library(gui_host STATIC "${GUI_DIR}/gui_format.c")
target_include_directories(gui_host PUBLIC "${GUI_DIR}/include")
target_link_libraries(gui_host PUBLIC meter_core_host)

add_library(feature_host STATIC "${FEATURE_DIR}/feature_auto_dim.c")
target_include_directories(feature_host PUBLIC "${FEATURE_DIR}/include")

# Compile the real production bsp_input.c with host-only stubs for the IDF
# GPIO/check headers (the debounce helper under test never touches GPIO).
add_library(input_host STATIC
  "${INPUT_DIR}/bsp_input.c"
  "${CMAKE_CURRENT_SOURCE_DIR}/host/stubs/stub_gpio.c"
)
target_include_directories(input_host PUBLIC
  "${INPUT_DIR}/include"
  "${CMAKE_CURRENT_SOURCE_DIR}/host/stubs"
)

foreach(t test_meter_parser test_meter_state test_meter_validate test_gui_regression test_feature_autodim test_input_debounce)
  add_executable(${t} "host/${t}.c")
  target_link_libraries(${t} PRIVATE meter_core_host gui_host feature_host input_host)
  add_test(NAME ${t} COMMAND ${t})
endforeach()
