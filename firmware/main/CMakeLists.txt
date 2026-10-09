idf_component_register(SRCS "main.c" "bsp.c" "cdm.c" "gui.c" "f9_temp.c"
    INCLUDE_DIRS "."
    REQUIRES json esp_lcd esp_driver_gpio esp_driver_tsens
        espressif__esp_lcd_panel_io_additions espressif__esp_lcd_st7701)
