idf_component_register(SRCS "app_main.c" "board_lcd.c"
                       INCLUDE_DIRS "."
                       REQUIRES driver esp_driver_usb_serial_jtag esp_lcd esp_timer json
                                meter_core idle_dim_policy vendor_st7701 vendor_panel_io_additions vendor_io_expander)
