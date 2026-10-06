set(VENDOR_COMPONENT "C:/Espressif/vendor/waveshare-esp32-s3-lcd-3.16/source/ESP32-S3-LCD-3.16-Demo/ESP-IDF/09_FactoryProgram/managed_components/espressif__esp_io_expander")
idf_component_register(SRCS "${VENDOR_COMPONENT}/esp_io_expander.c"
                       INCLUDE_DIRS "${VENDOR_COMPONENT}/include"
                       PRIV_REQUIRES esp_driver_gpio)
