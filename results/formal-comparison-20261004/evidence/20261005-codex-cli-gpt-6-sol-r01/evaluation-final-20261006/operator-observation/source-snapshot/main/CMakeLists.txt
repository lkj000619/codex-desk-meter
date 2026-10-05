idf_component_register(SRCS "main.c" "receiver.c" "board.c" "feature.c" INCLUDE_DIRS "." REQUIRES esp_lcd driver json esp_timer esp_psram)
