idf_component_register(SRCS "main.c" "bsp.c" "cdm.c" "gui.c" "f9_temp.c"
    INCLUDE_DIRS "."
    REQUIRES json esp_lcd esp_timer esp_driver_gpio esp_driver_tsens esp_driver_usb_serial_jtag
        espressif__esp_lcd_panel_io_additions espressif__esp_lcd_st7701)
