idf_component_register(
  SRCS "main.c"
  INCLUDE_DIRS "."
  REQUIRES "meter_core" "bsp_lcd" "bsp_input" "gui" "feature_auto_dim"
           "driver" "esp_driver_usb_serial_jtag" "esp_timer" "nvs_flash" "esp_lcd"
)
