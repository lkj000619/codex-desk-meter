set(VENDOR_COMPONENT "C:/Espressif/vendor/waveshare-esp32-s3-lcd-3.16/source/ESP32-S3-LCD-3.16-Demo/ESP-IDF/09_FactoryProgram/managed_components/espressif__esp_lcd_panel_io_additions")
idf_component_register(SRCS "${VENDOR_COMPONENT}/esp_lcd_panel_io_3wire_spi.c"
                       INCLUDE_DIRS "${VENDOR_COMPONENT}/include"
                       PRIV_REQUIRES driver
                       REQUIRES esp_lcd vendor_io_expander)
target_compile_definitions(${COMPONENT_LIB} PRIVATE
                           ESP_LCD_PANEL_IO_ADDITIONS_VER_MAJOR=1
                           ESP_LCD_PANEL_IO_ADDITIONS_VER_MINOR=0
                           ESP_LCD_PANEL_IO_ADDITIONS_VER_PATCH=1)
