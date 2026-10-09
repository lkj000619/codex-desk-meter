#pragma once
#include <stdint.h>
#include "esp_err.h"

// The RGB DMA framebuffer is physical 320x820; GUI coordinates are landscape 820x320.
esp_err_t bsp_init(void);
void bsp_pixel(int x, int y, uint16_t rgb565);
void bsp_fill(int x, int y, int w, int h, uint16_t rgb565);
int bsp_boot_level(void);
