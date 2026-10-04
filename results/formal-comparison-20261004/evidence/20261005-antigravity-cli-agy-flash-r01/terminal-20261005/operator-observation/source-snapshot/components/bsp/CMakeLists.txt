idf_component_register(SRCS "src/bsp_lcd.c"
                             "src/bsp_button.c"
                             "src/bsp_imu.c"
                             "src/bsp_serial.c"
                       INCLUDE_DIRS "include"
                       REQUIRES esp_lcd esp_driver_ledc esp_driver_i2c esp_driver_uart esp_timer meter_core)
