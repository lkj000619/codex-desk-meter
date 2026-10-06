idf_component_register(SRCS "main.c"
                       INCLUDE_DIRS "."
                       REQUIRES meter_core bsp esp_timer esp_lcd esp_driver_ledc esp_driver_i2c esp_driver_uart)
