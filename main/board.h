#pragma once
#include <stdint.h>
#include <stdbool.h>
bool board_start(void);
void board_clear(uint16_t color);
void board_rect(int x,int y,int w,int h,uint16_t color);
void board_text(int x,int y,const char *s,uint16_t color,int scale);
void board_present(void);
bool board_boot_pressed(void);
void board_brightness(uint8_t value);
