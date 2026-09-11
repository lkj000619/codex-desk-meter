idf_component_register(
    SRCS "main.c" "display_ui.c" "board_input.c" "fixture_data.c"
    INCLUDE_DIRS "."
    PRIV_REQUIRES meter imu_gesture esp_lcd_st7701 esp_lcd_panel_io_additions esp_timer driver nvs_flash json
)
