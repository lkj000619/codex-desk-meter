idf_component_register(
    SRCS "main.c" "cdm_receiver.c" "cdm_display.c" "cdm_rtc.c"
    INCLUDE_DIRS "."
    REQUIRES driver esp_timer esp_lcd esp_lcd_st7701 esp_lcd_panel_io_additions json)
