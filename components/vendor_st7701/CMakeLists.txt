set(VENDOR_COMPONENT "C:/Espressif/vendor/waveshare-esp32-s3-lcd-3.16/source/ESP32-S3-LCD-3.16-Demo/ESP-IDF/09_FactoryProgram/managed_components/espressif__esp_lcd_st7701")
idf_component_register(SRCS "${VENDOR_COMPONENT}/esp_lcd_st7701.c"
                            "${VENDOR_COMPONENT}/esp_lcd_st7701_rgb.c"
                            "${VENDOR_COMPONENT}/esp_lcd_st7701_mipi.c"
                       INCLUDE_DIRS "${VENDOR_COMPONENT}/include"
                       PRIV_INCLUDE_DIRS "${VENDOR_COMPONENT}/priv_include"
                       REQUIRES esp_lcd driver)
target_compile_definitions(${COMPONENT_LIB} PRIVATE
                           ESP_LCD_ST7701_VER_MAJOR=1
                           ESP_LCD_ST7701_VER_MINOR=1
                           ESP_LCD_ST7701_VER_PATCH=5)
