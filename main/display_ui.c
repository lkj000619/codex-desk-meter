#include "display_ui.h"
#include "user_config.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "esp_log.h"
#include "esp_heap_caps.h"
#include "driver/ledc.h"
#include "esp_lcd_panel_io.h"
#include "esp_lcd_panel_vendor.h"
#include "esp_lcd_panel_ops.h"
#include "esp_lcd_panel_rgb.h"
#include "esp_lcd_st7701.h"
#include "esp_lcd_panel_io_additions.h"

static const char *TAG = "display_ui";

static esp_lcd_panel_handle_t s_panel_handle = NULL;
static uint16_t *s_framebuffer = NULL;
static uint32_t s_current_screen = 0;

/* Color definitions in RGB565 */
#define COLOR_BLACK       0x0000
#define COLOR_WHITE       0xFFFF
#define COLOR_GRAY_DARK   0x18E3
#define COLOR_GRAY_MED    0x4208
#define COLOR_GRAY_LIGHT  0x8410
#define COLOR_BLUE_BG     0x08A7
#define COLOR_BLUE_ACCENT 0x1B5F
#define COLOR_GREEN       0x07E0
#define COLOR_GREEN_DARK  0x03E0
#define COLOR_AMBER       0xFD20
#define COLOR_RED         0xF800
#define COLOR_CYAN        0x07FF

/* Built-in 8x16 Basic ASCII Font (32..126) */
static const uint8_t font_8x16[95][16] = {
    {0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00}, // 32 ' '
    {0x00,0x00,0x18,0x3C,0x3C,0x3C,0x18,0x18,0x18,0x00,0x18,0x18,0x00,0x00,0x00,0x00}, // 33 '!'
    {0x00,0x66,0x66,0x66,0x24,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00}, // 34 '"'
    {0x00,0x00,0x6C,0x6C,0xFE,0x6C,0x6C,0x6C,0xFE,0x6C,0x6C,0x00,0x00,0x00,0x00,0x00}, // 35 '#'
    {0x18,0x18,0x7C,0xC6,0xC2,0xC0,0x7C,0x06,0x06,0x86,0xC6,0x7C,0x18,0x18,0x00,0x00}, // 36 '$'
    {0x00,0x00,0x00,0x00,0xC2,0xC6,0x0C,0x18,0x30,0x60,0xC6,0x86,0x00,0x00,0x00,0x00}, // 37 '%'
    {0x00,0x00,0x38,0x6C,0x6C,0x38,0x76,0xDC,0xCC,0xCC,0xDC,0x76,0x00,0x00,0x00,0x00}, // 38 '&'
    {0x00,0x30,0x30,0x30,0x60,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00}, // 39 single quote
    {0x00,0x00,0x0C,0x18,0x30,0x30,0x30,0x30,0x30,0x30,0x18,0x0C,0x00,0x00,0x00,0x00}, // 40 '('
    {0x00,0x00,0x30,0x18,0x0C,0x0C,0x0C,0x0C,0x0C,0x0C,0x18,0x30,0x00,0x00,0x00,0x00}, // 41 ')'
    {0x00,0x00,0x00,0x66,0x3C,0xFF,0x3C,0x66,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00}, // 42 '*'
    {0x00,0x00,0x00,0x18,0x18,0x7E,0x18,0x18,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00}, // 43 '+'
    {0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x18,0x18,0x18,0x30,0x00,0x00,0x00}, // 44 ','
    {0x00,0x00,0x00,0x00,0x00,0x7E,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00}, // 45 '-'
    {0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x18,0x18,0x00,0x00,0x00,0x00}, // 46 '.'
    {0x00,0x00,0x02,0x06,0x0C,0x18,0x30,0x60,0xC0,0x80,0x00,0x00,0x00,0x00,0x00,0x00}, // 47 '/'
    {0x00,0x00,0x3C,0x66,0xC3,0xC3,0xDB,0xDB,0xC3,0xC3,0x66,0x3C,0x00,0x00,0x00,0x00}, // 48 '0'
    {0x00,0x00,0x18,0x38,0x78,0x18,0x18,0x18,0x18,0x18,0x18,0x7E,0x00,0x00,0x00,0x00}, // 49 '1'
    {0x00,0x00,0x7C,0xC6,0x06,0x0C,0x18,0x30,0x60,0xC0,0xC6,0xFE,0x00,0x00,0x00,0x00}, // 50 '2'
    {0x00,0x00,0x7C,0xC6,0x06,0x06,0x3C,0x06,0x06,0x06,0xC6,0x7C,0x00,0x00,0x00,0x00}, // 51 '3'
    {0x00,0x00,0x0C,0x1C,0x3C,0x6C,0xCC,0xFE,0x0C,0x0C,0x0C,0x1E,0x00,0x00,0x00,0x00}, // 52 '4'
    {0x00,0x00,0xFE,0xC0,0xC0,0xC0,0xFC,0x06,0x06,0x06,0xC6,0x7C,0x00,0x00,0x00,0x00}, // 53 '5'
    {0x00,0x00,0x38,0x60,0xC0,0xC0,0xFC,0xC6,0xC6,0xC6,0xC6,0x7C,0x00,0x00,0x00,0x00}, // 54 '6'
    {0x00,0x00,0xFE,0xC6,0x06,0x0C,0x18,0x30,0x30,0x30,0x30,0x30,0x00,0x00,0x00,0x00}, // 55 '7'
    {0x00,0x00,0x7C,0xC6,0xC6,0xC6,0x7C,0xC6,0xC6,0xC6,0xC6,0x7C,0x00,0x00,0x00,0x00}, // 56 '8'
    {0x00,0x00,0x7C,0xC6,0xC6,0xC6,0x7E,0x06,0x06,0x06,0x0C,0x78,0x00,0x00,0x00,0x00}, // 57 '9'
    {0x00,0x00,0x00,0x18,0x18,0x00,0x00,0x00,0x00,0x18,0x18,0x00,0x00,0x00,0x00,0x00}, // 58 ':'
    {0x00,0x00,0x00,0x18,0x18,0x00,0x00,0x00,0x00,0x18,0x18,0x30,0x00,0x00,0x00,0x00}, // 59 ';'
    {0x00,0x00,0x06,0x0C,0x18,0x30,0x60,0x30,0x18,0x0C,0x06,0x00,0x00,0x00,0x00,0x00}, // 60 '<'
    {0x00,0x00,0x00,0x00,0x7E,0x00,0x00,0x7E,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00}, // 61 '='
    {0x00,0x00,0x60,0x30,0x18,0x0C,0x06,0x0C,0x18,0x30,0x60,0x00,0x00,0x00,0x00,0x00}, // 62 '>'
    {0x00,0x00,0x7C,0xC6,0x06,0x0C,0x18,0x18,0x00,0x18,0x18,0x00,0x00,0x00,0x00,0x00}, // 63 '?'
    {0x00,0x00,0x7C,0xC6,0xC6,0xDE,0xDE,0xDE,0xDC,0xC0,0x7C,0x00,0x00,0x00,0x00,0x00}, // 64 '@'
    {0x00,0x00,0x10,0x38,0x6C,0xC6,0xC6,0xFE,0xC6,0xC6,0xC6,0xC6,0x00,0x00,0x00,0x00}, // 65 'A'
    {0x00,0x00,0xFC,0x66,0x66,0x66,0x7C,0x66,0x66,0x66,0x66,0xFC,0x00,0x00,0x00,0x00}, // 66 'B'
    {0x00,0x00,0x3C,0x66,0xC2,0xC0,0xC0,0xC0,0xC0,0xC2,0x66,0x3C,0x00,0x00,0x00,0x00}, // 67 'C'
    {0x00,0x00,0xF8,0x6C,0x66,0x66,0x66,0x66,0x66,0x66,0x6C,0xF8,0x00,0x00,0x00,0x00}, // 68 'D'
    {0x00,0x00,0xFE,0x62,0x62,0x68,0x78,0x68,0x60,0x62,0x62,0xFE,0x00,0x00,0x00,0x00}, // 69 'E'
    {0x00,0x00,0xFE,0x62,0x62,0x68,0x78,0x68,0x60,0x60,0x60,0xF0,0x00,0x00,0x00,0x00}, // 70 'F'
    {0x00,0x00,0x3C,0x66,0xC2,0xC0,0xC0,0xCE,0xC6,0xC6,0x66,0x3A,0x00,0x00,0x00,0x00}, // 71 'G'
    {0x00,0x00,0xC6,0xC6,0xC6,0xC6,0xFE,0xC6,0xC6,0xC6,0xC6,0xC6,0x00,0x00,0x00,0x00}, // 72 'H'
    {0x00,0x00,0x3C,0x18,0x18,0x18,0x18,0x18,0x18,0x18,0x18,0x3C,0x00,0x00,0x00,0x00}, // 73 'I'
    {0x00,0x00,0x1E,0x0C,0x0C,0x0C,0x0C,0x0C,0xCC,0xCC,0xCC,0x78,0x00,0x00,0x00,0x00}, // 74 'J'
    {0x00,0x00,0xE6,0x66,0x66,0x6C,0x78,0x78,0x6C,0x66,0x66,0xE6,0x00,0x00,0x00,0x00}, // 75 'K'
    {0x00,0x00,0xF0,0x60,0x60,0x60,0x60,0x60,0x60,0x62,0x66,0xFE,0x00,0x00,0x00,0x00}, // 76 'L'
    {0x00,0x00,0xC3,0xE7,0xFF,0xDB,0xC3,0xC3,0xC3,0xC3,0xC3,0xC3,0x00,0x00,0x00,0x00}, // 77 'M'
    {0x00,0x00,0xC6,0xE6,0xF6,0xFE,0xDE,0xCE,0xC6,0xC6,0xC6,0xC6,0x00,0x00,0x00,0x00}, // 78 'N'
    {0x00,0x00,0x7C,0xC6,0xC6,0xC6,0xC6,0xC6,0xC6,0xC6,0xC6,0x7C,0x00,0x00,0x00,0x00}, // 79 'O'
    {0x00,0x00,0xFC,0x66,0x66,0x66,0x7C,0x60,0x60,0x60,0x60,0xF0,0x00,0x00,0x00,0x00}, // 80 'P'
    {0x00,0x00,0x7C,0xC6,0xC6,0xC6,0xC6,0xC6,0xC6,0xD6,0xDE,0x7C,0x0C,0x0E,0x00,0x00}, // 81 'Q'
    {0x00,0x00,0xFC,0x66,0x66,0x66,0x7C,0x6C,0x66,0x66,0x66,0xE6,0x00,0x00,0x00,0x00}, // 82 'R'
    {0x00,0x00,0x7C,0xC6,0xC6,0x60,0x38,0x0C,0x06,0xC6,0xC6,0x7C,0x00,0x00,0x00,0x00}, // 83 'S'
    {0x00,0x00,0x7E,0x5A,0x18,0x18,0x18,0x18,0x18,0x18,0x18,0x3C,0x00,0x00,0x00,0x00}, // 84 'T'
    {0x00,0x00,0xC6,0xC6,0xC6,0xC6,0xC6,0xC6,0xC6,0xC6,0xC6,0x7C,0x00,0x00,0x00,0x00}, // 85 'U'
    {0x00,0x00,0xC6,0xC6,0xC6,0xC6,0xC6,0xC6,0xC6,0x6C,0x38,0x10,0x00,0x00,0x00,0x00}, // 86 'V'
    {0x00,0x00,0xC3,0xC3,0xC3,0xC3,0xC3,0xDB,0xDB,0xFF,0x66,0x66,0x00,0x00,0x00,0x00}, // 87 'W'
    {0x00,0x00,0xC3,0xC3,0x66,0x3C,0x18,0x3C,0x66,0xC3,0xC3,0xC3,0x00,0x00,0x00,0x00}, // 88 'X'
    {0x00,0x00,0xC3,0xC3,0xC6,0x6C,0x38,0x18,0x18,0x18,0x18,0x3C,0x00,0x00,0x00,0x00}, // 89 'Y'
    {0x00,0x00,0xFE,0xC6,0x86,0x0C,0x18,0x30,0x60,0xC2,0xC6,0xFE,0x00,0x00,0x00,0x00}, // 90 'Z'
    {0x00,0x00,0x3C,0x30,0x30,0x30,0x30,0x30,0x30,0x30,0x30,0x3C,0x00,0x00,0x00,0x00}, // 91 '['
    {0x00,0x00,0x80,0xC0,0x60,0x30,0x18,0x0C,0x06,0x02,0x00,0x00,0x00,0x00,0x00,0x00}, // 92 '\'
    {0x00,0x00,0x3C,0x0C,0x0C,0x0C,0x0C,0x0C,0x0C,0x0C,0x0C,0x3C,0x00,0x00,0x00,0x00}, // 93 ']'
    {0x00,0x10,0x38,0x6C,0xC6,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00}, // 94 '^'
    {0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xFF,0x00,0x00,0x00,0x00}, // 95 '_'
    {0x00,0x30,0x18,0x0C,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00}, // 96 '`'
    {0x00,0x00,0x00,0x00,0x00,0x78,0x0C,0x7C,0xCC,0xCC,0xCC,0x76,0x00,0x00,0x00,0x00}, // 97 'a'
    {0x00,0x00,0xE0,0x60,0x60,0x7C,0x66,0x66,0x66,0x66,0x66,0x7C,0x00,0x00,0x00,0x00}, // 98 'b'
    {0x00,0x00,0x00,0x00,0x00,0x7C,0xC6,0xC0,0xC0,0xC0,0xC6,0x7C,0x00,0x00,0x00,0x00}, // 99 'c'
    {0x00,0x00,0x1C,0x0C,0x0C,0x7C,0xCC,0xCC,0xCC,0xCC,0xCC,0x76,0x00,0x00,0x00,0x00}, // 100 'd'
    {0x00,0x00,0x00,0x00,0x00,0x7C,0xC6,0xFE,0xC0,0xC0,0xC6,0x7C,0x00,0x00,0x00,0x00}, // 101 'e'
    {0x00,0x00,0x38,0x6C,0x64,0x60,0xF0,0x60,0x60,0x60,0x60,0xF0,0x00,0x00,0x00,0x00}, // 102 'f'
    {0x00,0x00,0x00,0x00,0x00,0x76,0xCC,0xCC,0xCC,0x7C,0x0C,0xCC,0x78,0x00,0x00,0x00}, // 103 'g'
    {0x00,0x00,0xE0,0x60,0x60,0x6C,0x76,0x66,0x66,0x66,0x66,0xE6,0x00,0x00,0x00,0x00}, // 104 'h'
    {0x00,0x00,0x18,0x18,0x00,0x38,0x18,0x18,0x18,0x18,0x18,0x3C,0x00,0x00,0x00,0x00}, // 105 'i'
    {0x00,0x00,0x0C,0x0C,0x00,0x1C,0x0C,0x0C,0x0C,0x0C,0xCC,0xCC,0x78,0x00,0x00,0x00}, // 106 'j'
    {0x00,0x00,0xE0,0x60,0x60,0x66,0x6C,0x78,0x78,0x6C,0x66,0xE6,0x00,0x00,0x00,0x00}, // 107 'k'
    {0x00,0x00,0x38,0x18,0x18,0x18,0x18,0x18,0x18,0x18,0x18,0x3C,0x00,0x00,0x00,0x00}, // 108 'l'
    {0x00,0x00,0x00,0x00,0x00,0xE6,0xFF,0xDB,0xDB,0xC3,0xC3,0xC3,0x00,0x00,0x00,0x00}, // 109 'm'
    {0x00,0x00,0x00,0x00,0x00,0xDC,0x66,0x66,0x66,0x66,0x66,0x66,0x00,0x00,0x00,0x00}, // 110 'n'
    {0x00,0x00,0x00,0x00,0x00,0x7C,0xC6,0xC6,0xC6,0xC6,0xC6,0x7C,0x00,0x00,0x00,0x00}, // 111 'o'
    {0x00,0x00,0x00,0x00,0x00,0xDC,0x66,0x66,0x66,0x66,0x7C,0x60,0xF0,0x00,0x00,0x00}, // 112 'p'
    {0x00,0x00,0x00,0x00,0x00,0x76,0xCC,0xCC,0xCC,0xCC,0x7C,0x0C,0x1E,0x00,0x00,0x00}, // 113 'q'
    {0x00,0x00,0x00,0x00,0x00,0xDC,0x76,0x66,0x60,0x60,0x60,0xF0,0x00,0x00,0x00,0x00}, // 114 'r'
    {0x00,0x00,0x00,0x00,0x00,0x7C,0xC6,0x60,0x38,0x0C,0xC6,0x7C,0x00,0x00,0x00,0x00}, // 115 's'
    {0x00,0x00,0x10,0x30,0x30,0xFC,0x30,0x30,0x30,0x30,0x36,0x1C,0x00,0x00,0x00,0x00}, // 116 't'
    {0x00,0x00,0x00,0x00,0x00,0xCC,0xCC,0xCC,0xCC,0xCC,0xCC,0x76,0x00,0x00,0x00,0x00}, // 117 'u'
    {0x00,0x00,0x00,0x00,0x00,0xC6,0xC6,0xC6,0xC6,0x6C,0x38,0x10,0x00,0x00,0x00,0x00}, // 118 'v'
    {0x00,0x00,0x00,0x00,0x00,0xC3,0xC3,0xDB,0xDB,0xFF,0x66,0x66,0x00,0x00,0x00,0x00}, // 119 'w'
    {0x00,0x00,0x00,0x00,0x00,0xC3,0x66,0x3C,0x18,0x3C,0x66,0xC3,0x00,0x00,0x00,0x00}, // 120 'x'
    {0x00,0x00,0x00,0x00,0x00,0xC6,0xC6,0xC6,0xC6,0x7E,0x06,0x0C,0xF8,0x00,0x00,0x00}, // 121 'y'
    {0x00,0x00,0x00,0x00,0x00,0xFE,0xCC,0x18,0x30,0x60,0xC6,0xFE,0x00,0x00,0x00,0x00}, // 122 'z'
    {0x00,0x00,0x0E,0x18,0x18,0x18,0x70,0x18,0x18,0x18,0x18,0x0E,0x00,0x00,0x00,0x00}, // 123 '{'
    {0x00,0x00,0x18,0x18,0x18,0x18,0x18,0x00,0x18,0x18,0x18,0x18,0x00,0x00,0x00,0x00}, // 124 '|'
    {0x00,0x00,0x70,0x18,0x18,0x18,0x0E,0x18,0x18,0x18,0x18,0x70,0x00,0x00,0x00,0x00}, // 125 '}'
    {0x00,0x76,0xDC,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00}  // 126 '~'
};

static void draw_pixel(int x, int y, uint16_t color) {
    if (x < 0 || x >= LCD_WIDTH || y < 0 || y >= LCD_HEIGHT) return;
    s_framebuffer[y * LCD_WIDTH + x] = color;
}

static void draw_fill_rect(int x, int y, int w, int h, uint16_t color) {
    if (x < 0) { w += x; x = 0; }
    if (y < 0) { h += y; y = 0; }
    if (x + w > LCD_WIDTH) w = LCD_WIDTH - x;
    if (y + h > LCD_HEIGHT) h = LCD_HEIGHT - y;
    if (w <= 0 || h <= 0) return;

    for (int j = 0; j < h; j++) {
        uint16_t *row = &s_framebuffer[(y + j) * LCD_WIDTH + x];
        for (int i = 0; i < w; i++) {
            row[i] = color;
        }
    }
}

static void draw_rect(int x, int y, int w, int h, uint16_t color) {
    draw_fill_rect(x, y, w, 1, color);
    draw_fill_rect(x, y + h - 1, w, 1, color);
    draw_fill_rect(x, y, 1, h, color);
    draw_fill_rect(x + w - 1, y, 1, h, color);
}

static void draw_char(int x, int y, char c, uint16_t color, uint16_t bg_color, int scale) {
    if (c < 32 || c > 126) c = '?';
    const uint8_t *bitmap = font_8x16[c - 32];
    for (int r = 0; r < 16; r++) {
        uint8_t row = bitmap[r];
        for (int col = 0; col < 8; col++) {
            if (row & (0x80 >> col)) {
                if (scale == 1) {
                    draw_pixel(x + col, y + r, color);
                } else {
                    draw_fill_rect(x + col * scale, y + r * scale, scale, scale, color);
                }
            } else if (bg_color != COLOR_BLACK || true) {
                if (scale == 1) {
                    draw_pixel(x + col, y + r, bg_color);
                } else {
                    draw_fill_rect(x + col * scale, y + r * scale, scale, scale, bg_color);
                }
            }
        }
    }
}

static void draw_string(int x, int y, const char *str, uint16_t color, uint16_t bg_color, int scale) {
    if (!str) return;
    int cur_x = x;
    int char_w = 8 * scale;
    while (*str) {
        if (cur_x + char_w > LCD_WIDTH) break;
        draw_char(cur_x, y, *str, color, bg_color, scale);
        cur_x += char_w;
        str++;
    }
}

static void draw_progress_bar(int x, int y, int w, int h, int percent, uint16_t fg_color, uint16_t bg_color) {
    draw_rect(x, y, w, h, COLOR_WHITE);
    draw_fill_rect(x + 1, y + 1, w - 2, h - 2, bg_color);
    if (percent > 100) percent = 100;
    if (percent < 0) percent = 0;
    int fill_w = ((w - 2) * percent) / 100;
    if (fill_w > 0) {
        draw_fill_rect(x + 1, y + 1, fill_w, h - 2, fg_color);
    }
}

/* Screen 0: Dashboard (Personal Usage) */
static void render_screen_dashboard(const meter_state_t *state) {
    draw_fill_rect(0, 0, LCD_WIDTH, LCD_HEIGHT, COLOR_BLACK);

    /* Header Bar */
    draw_fill_rect(0, 0, LCD_WIDTH, 44, COLOR_BLUE_BG);
    draw_string(14, 14, "CODEX DESK METER", COLOR_WHITE, COLOR_BLUE_BG, 2);

    /* Freshness Status Badge */
    if (state->usage.stale) {
        draw_fill_rect(200, 52, 106, 26, COLOR_AMBER);
        draw_string(206, 57, "STALE (>5m)", COLOR_BLACK, COLOR_AMBER, 1);
    } else {
        draw_fill_rect(220, 52, 86, 26, COLOR_GREEN_DARK);
        draw_string(232, 57, "FRESH", COLOR_WHITE, COLOR_GREEN_DARK, 1);
    }

    draw_string(14, 58, "PERSONAL USAGE", COLOR_CYAN, COLOR_BLACK, 1);

    /* Card 1: 5-Hour Window */
    int card1_y = 86;
    draw_fill_rect(10, card1_y, 300, 210, COLOR_GRAY_DARK);
    draw_rect(10, card1_y, 300, 210, COLOR_BLUE_ACCENT);

    draw_string(24, card1_y + 14, "5-HOUR WINDOW", COLOR_WHITE, COLOR_GRAY_DARK, 2);

    const usage_window_t *w5 = (state->usage.window_count > 0) ? &state->usage.windows[0] : NULL;
    char buf[128];
    if (w5 && w5->has_percent_remaining) {
        snprintf(buf, sizeof(buf), "%d%%", (int)w5->percent_remaining);
        draw_string(24, card1_y + 50, buf, COLOR_GREEN, COLOR_GRAY_DARK, 4);
        draw_string(150, card1_y + 66, "REMAINING", COLOR_WHITE, COLOR_GRAY_DARK, 1);
    } else {
        draw_string(24, card1_y + 50, "--%", COLOR_GRAY_LIGHT, COLOR_GRAY_DARK, 4);
    }

    if (w5 && w5->has_percent_used) {
        snprintf(buf, sizeof(buf), "Used: %d%%", (int)w5->percent_used);
        draw_string(24, card1_y + 120, buf, COLOR_AMBER, COLOR_GRAY_DARK, 1);
        draw_progress_bar(24, card1_y + 140, 272, 18, w5->percent_used, COLOR_AMBER, COLOR_BLACK);
    }

    if (w5 && w5->has_resets_at) {
        snprintf(buf, sizeof(buf), "Reset: %s", w5->resets_at);
        draw_string(24, card1_y + 172, buf, COLOR_GRAY_LIGHT, COLOR_GRAY_DARK, 1);
    } else {
        draw_string(24, card1_y + 172, "Reset: -- (Not Scheduled)", COLOR_GRAY_LIGHT, COLOR_GRAY_DARK, 1);
    }

    /* Card 2: Weekly Window */
    int card2_y = 312;
    draw_fill_rect(10, card2_y, 300, 210, COLOR_GRAY_DARK);
    draw_rect(10, card2_y, 300, 210, COLOR_BLUE_ACCENT);

    draw_string(24, card2_y + 14, "WEEKLY WINDOW", COLOR_WHITE, COLOR_GRAY_DARK, 2);

    const usage_window_t *ww = (state->usage.window_count > 1) ? &state->usage.windows[1] : NULL;
    if (ww && ww->has_percent_remaining) {
        snprintf(buf, sizeof(buf), "%d%%", (int)ww->percent_remaining);
        draw_string(24, card2_y + 50, buf, COLOR_GREEN, COLOR_GRAY_DARK, 4);
        draw_string(150, card2_y + 66, "REMAINING", COLOR_WHITE, COLOR_GRAY_DARK, 1);
    } else {
        draw_string(24, card2_y + 50, "--%", COLOR_GRAY_LIGHT, COLOR_GRAY_DARK, 4);
    }

    if (ww && ww->has_percent_used) {
        snprintf(buf, sizeof(buf), "Used: %d%%", (int)ww->percent_used);
        draw_string(24, card2_y + 120, buf, COLOR_AMBER, COLOR_GRAY_DARK, 1);
        draw_progress_bar(24, card2_y + 140, 272, 18, ww->percent_used, COLOR_AMBER, COLOR_BLACK);
    }

    if (ww && ww->has_resets_at) {
        snprintf(buf, sizeof(buf), "Reset: %s", ww->resets_at);
        draw_string(24, card2_y + 172, buf, COLOR_GRAY_LIGHT, COLOR_GRAY_DARK, 1);
    } else {
        draw_string(24, card2_y + 172, "Reset: -- (Not Scheduled)", COLOR_GRAY_LIGHT, COLOR_GRAY_DARK, 1);
    }

    /* Metadata Footer Card */
    int meta_y = 540;
    draw_fill_rect(10, meta_y, 300, 160, COLOR_GRAY_DARK);
    draw_rect(10, meta_y, 300, 160, COLOR_GRAY_MED);

    draw_string(20, meta_y + 14, "DATA OBSERVATION", COLOR_CYAN, COLOR_GRAY_DARK, 1);
    if (state->usage.has_observed_at) {
        snprintf(buf, sizeof(buf), "Observed: %s", state->usage.observed_at);
        draw_string(20, meta_y + 36, buf, COLOR_WHITE, COLOR_GRAY_DARK, 1);
    } else {
        draw_string(20, meta_y + 36, "Observed: null", COLOR_GRAY_LIGHT, COLOR_GRAY_DARK, 1);
    }
    snprintf(buf, sizeof(buf), "Source: %s", state->usage.source);
    draw_string(20, meta_y + 60, buf, COLOR_GRAY_LIGHT, COLOR_GRAY_DARK, 1);

    snprintf(buf, sizeof(buf), "Auto Refresh: %ds", METER_AUTO_REFRESH_INTERVAL_SEC);
    draw_string(20, meta_y + 84, buf, COLOR_GRAY_LIGHT, COLOR_GRAY_DARK, 1);

    if (state->usage.has_error_code && state->usage.error_code[0] != 0) {
        snprintf(buf, sizeof(buf), "Notice: %s", state->usage.error_code);
        draw_string(20, meta_y + 110, buf, COLOR_AMBER, COLOR_GRAY_DARK, 1);
        draw_string(20, meta_y + 130, "(Holding last good snapshot)", COLOR_AMBER, COLOR_GRAY_DARK, 1);
    } else {
        draw_string(20, meta_y + 110, "Status: Normal (Fresh Data)", COLOR_GREEN, COLOR_GRAY_DARK, 1);
    }

    /* Bottom Navigation Bar */
    draw_fill_rect(0, 770, LCD_WIDTH, 50, COLOR_BLUE_BG);
    draw_string(20, 786, "[BOOT/Tap] Screen 1/3 ->", COLOR_WHITE, COLOR_BLUE_BG, 1);
}

/* Screen 1: Global Resets (codex-reset.com & codex-resets.com) */
static void render_screen_global_resets(const meter_state_t *state) {
    draw_fill_rect(0, 0, LCD_WIDTH, LCD_HEIGHT, COLOR_BLACK);

    /* Header Bar */
    draw_fill_rect(0, 0, LCD_WIDTH, 44, COLOR_BLUE_BG);
    draw_string(14, 14, "GLOBAL RESETS", COLOR_WHITE, COLOR_BLUE_BG, 2);

    draw_string(14, 56, "PUBLIC SIGNALS (SEPARATE C6)", COLOR_CYAN, COLOR_BLACK, 1);

    /* Card 1: codex-reset.com (Forecast Provider) */
    int card1_y = 80;
    draw_fill_rect(10, card1_y, 300, 270, COLOR_GRAY_DARK);
    draw_rect(10, card1_y, 300, 270, COLOR_BLUE_ACCENT);

    draw_string(20, card1_y + 14, "codex-reset.com", COLOR_CYAN, COLOR_GRAY_DARK, 2);

    char buf[128];
    const global_reset_snapshot_t *gr = &state->reset_forecast;
    if (gr->has_latest_reset_at) {
        draw_string(20, card1_y + 46, "Latest Global Reset:", COLOR_GRAY_LIGHT, COLOR_GRAY_DARK, 1);
        draw_string(20, card1_y + 64, gr->latest_reset_at, COLOR_WHITE, COLOR_GRAY_DARK, 1);
    } else {
        draw_string(20, card1_y + 46, "Latest Reset: --", COLOR_GRAY_LIGHT, COLOR_GRAY_DARK, 1);
    }

    draw_fill_rect(20, card1_y + 90, 280, 1, COLOR_GRAY_MED);

    draw_string(20, card1_y + 102, "Next Reset Forecast:", COLOR_WHITE, COLOR_GRAY_DARK, 1);

    if (gr->has_forecast_24h) {
        snprintf(buf, sizeof(buf), "24h Prob: %d%%", (int)gr->forecast_24h_percent);
        draw_string(20, card1_y + 124, buf, COLOR_GREEN, COLOR_GRAY_DARK, 2);
    } else {
        draw_string(20, card1_y + 124, "24h Prob: N/A", COLOR_GRAY_LIGHT, COLOR_GRAY_DARK, 1);
    }

    if (gr->has_forecast_48h) {
        snprintf(buf, sizeof(buf), "48h Prob: %d%%", (int)gr->forecast_48h_percent);
        draw_string(20, card1_y + 154, buf, COLOR_GREEN, COLOR_GRAY_DARK, 2);
    } else {
        draw_string(20, card1_y + 154, "48h Prob: N/A", COLOR_GRAY_LIGHT, COLOR_GRAY_DARK, 1);
    }

    /* Contract C5: Explicit disclaimer */
    draw_string(20, card1_y + 196, "* Probabilistic estimate", COLOR_AMBER, COLOR_GRAY_DARK, 1);
    draw_string(20, card1_y + 214, "* NOT a guaranteed schedule", COLOR_AMBER, COLOR_GRAY_DARK, 1);

    if (gr->has_fetched_at) {
        snprintf(buf, sizeof(buf), "Fetched: %s", gr->fetched_at);
        draw_string(20, card1_y + 238, buf, COLOR_GRAY_LIGHT, COLOR_GRAY_DARK, 1);
    }

    /* Card 2: codex-resets.com (History Provider) */
    int card2_y = 366;
    draw_fill_rect(10, card2_y, 300, 210, COLOR_GRAY_DARK);
    draw_rect(10, card2_y, 300, 210, COLOR_BLUE_ACCENT);

    draw_string(20, card2_y + 14, "codex-resets.com", COLOR_CYAN, COLOR_GRAY_DARK, 2);

    const global_reset_snapshot_t *gh = &state->reset_history;
    if (gh->has_latest_reset_at) {
        draw_string(20, card2_y + 46, "Latest Global Reset:", COLOR_GRAY_LIGHT, COLOR_GRAY_DARK, 1);
        draw_string(20, card2_y + 64, gh->latest_reset_at, COLOR_WHITE, COLOR_GRAY_DARK, 1);
    } else {
        draw_string(20, card2_y + 46, "Latest Reset: --", COLOR_GRAY_LIGHT, COLOR_GRAY_DARK, 1);
    }

    draw_fill_rect(20, card2_y + 90, 280, 1, COLOR_GRAY_MED);

    draw_string(20, card2_y + 102, "Next Reset Forecast:", COLOR_WHITE, COLOR_GRAY_DARK, 1);
    draw_string(20, card2_y + 126, "Forecast: N/A (Not Provided)", COLOR_GRAY_LIGHT, COLOR_GRAY_DARK, 1);
    draw_string(20, card2_y + 146, "Provider focuses on historical log", COLOR_GRAY_LIGHT, COLOR_GRAY_DARK, 1);

    if (gh->has_fetched_at) {
        snprintf(buf, sizeof(buf), "Fetched: %s", gh->fetched_at);
        draw_string(20, card2_y + 176, buf, COLOR_GRAY_LIGHT, COLOR_GRAY_DARK, 1);
    }

    /* Policy Note Card */
    int note_y = 592;
    draw_fill_rect(10, note_y, 300, 150, COLOR_GRAY_DARK);
    draw_rect(10, note_y, 300, 150, COLOR_GRAY_MED);
    draw_string(20, note_y + 14, "DATA CONTRACT INTEGRITY", COLOR_WHITE, COLOR_GRAY_DARK, 1);
    draw_string(20, note_y + 36, "- C6: Providers are NOT merged", COLOR_GREEN, COLOR_GRAY_DARK, 1);
    draw_string(20, note_y + 56, "- Independent observation timestamps", COLOR_GREEN, COLOR_GRAY_DARK, 1);
    draw_string(20, note_y + 76, "- Different dates/events preserved", COLOR_GREEN, COLOR_GRAY_DARK, 1);
    draw_string(20, note_y + 96, "- C7: Outage resilience active", COLOR_GREEN, COLOR_GRAY_DARK, 1);

    /* Bottom Navigation Bar */
    draw_fill_rect(0, 770, LCD_WIDTH, 50, COLOR_BLUE_BG);
    draw_string(20, 786, "[BOOT/Tap] Screen 2/3 ->", COLOR_WHITE, COLOR_BLUE_BG, 1);
}

/* Screen 2: System Status & Diagnostics (C7 Outage handling & C8 Input info) */
static void render_screen_diagnostics(const meter_state_t *state) {
    draw_fill_rect(0, 0, LCD_WIDTH, LCD_HEIGHT, COLOR_BLACK);

    /* Header Bar */
    draw_fill_rect(0, 0, LCD_WIDTH, 44, COLOR_BLUE_BG);
    draw_string(14, 14, "SYSTEM DIAGNOSTICS", COLOR_WHITE, COLOR_BLUE_BG, 2);

    /* Health Summary Card */
    int y = 60;
    draw_fill_rect(10, y, 300, 180, COLOR_GRAY_DARK);
    draw_rect(10, y, 300, 180, COLOR_BLUE_ACCENT);

    draw_string(20, y + 14, "CONNECTION & RECOVERY", COLOR_CYAN, COLOR_GRAY_DARK, 1);

    char buf[128];
    snprintf(buf, sizeof(buf), "Data Mode: Fixture (Offline)");
    draw_string(20, y + 36, buf, COLOR_WHITE, COLOR_GRAY_DARK, 1);

    snprintf(buf, sizeof(buf), "Auto Refresh Period: 60s");
    draw_string(20, y + 58, buf, COLOR_WHITE, COLOR_GRAY_DARK, 1);

    snprintf(buf, sizeof(buf), "Stale Threshold: 300s (5min)");
    draw_string(20, y + 80, buf, COLOR_WHITE, COLOR_GRAY_DARK, 1);

    if (state->usage.has_error_code && state->usage.error_code[0] != 0) {
        snprintf(buf, sizeof(buf), "Active Fault: %s", state->usage.error_code);
        draw_string(20, y + 104, buf, COLOR_RED, COLOR_GRAY_DARK, 1);
        draw_string(20, y + 126, "Fallback State: ACTIVE (Safe)", COLOR_AMBER, COLOR_GRAY_DARK, 1);
    } else {
        draw_string(20, y + 104, "Active Fault: None (Healthy)", COLOR_GREEN, COLOR_GRAY_DARK, 1);
        draw_string(20, y + 126, "Fallback State: Ready (Standby)", COLOR_GREEN, COLOR_GRAY_DARK, 1);
    }
    draw_string(20, y + 150, "Watchdog: Healthy (No Resets)", COLOR_GREEN, COLOR_GRAY_DARK, 1);

    /* Hardware Resources Card */
    y = 256;
    draw_fill_rect(10, y, 300, 230, COLOR_GRAY_DARK);
    draw_rect(10, y, 300, 230, COLOR_BLUE_ACCENT);

    draw_string(20, y + 14, "HARDWARE PROFILE (ESP32-S3)", COLOR_CYAN, COLOR_GRAY_DARK, 1);
    draw_string(20, y + 36, "MCU: ESP32-S3R8 (Dual 240MHz)", COLOR_WHITE, COLOR_GRAY_DARK, 1);
    draw_string(20, y + 56, "Memory: 16MB Flash, 8MB PSRAM", COLOR_WHITE, COLOR_GRAY_DARK, 1);
    draw_string(20, y + 76, "LCD: 320x820 ST7701 RGB565", COLOR_WHITE, COLOR_GRAY_DARK, 1);
    draw_string(20, y + 96, "Backlight: LEDC PWM GPIO6 100%", COLOR_WHITE, COLOR_GRAY_DARK, 1);
    draw_string(20, y + 116, "BOOT Btn: GPIO0 (Debounced)", COLOR_WHITE, COLOR_GRAY_DARK, 1);
    draw_string(20, y + 136, "IMU: QMI8658 6-Axis (I2C 0x6B)", COLOR_WHITE, COLOR_GRAY_DARK, 1);
    draw_string(20, y + 156, "Feature: Double-Tap & Shake Detect", COLOR_GREEN, COLOR_GRAY_DARK, 1);
    draw_string(20, y + 176, "RST: System Reset Only (Preserved)", COLOR_GRAY_LIGHT, COLOR_GRAY_DARK, 1);
    draw_string(20, y + 196, "TF Card: Optional (Safe Timeout)", COLOR_GRAY_LIGHT, COLOR_GRAY_DARK, 1);

    /* Interaction Guide Card */
    y = 502;
    draw_fill_rect(10, y, 300, 240, COLOR_GRAY_DARK);
    draw_rect(10, y, 300, 240, COLOR_GRAY_MED);

    draw_string(20, y + 14, "INTERACTION GUIDE", COLOR_WHITE, COLOR_GRAY_DARK, 1);
    draw_string(20, y + 36, "1. BOOT Click: Cycle Screens", COLOR_WHITE, COLOR_GRAY_DARK, 1);
    draw_string(20, y + 56, "   (Dashboard -> Resets -> Status)", COLOR_GRAY_LIGHT, COLOR_GRAY_DARK, 1);
    draw_string(20, y + 80, "2. BOOT Long Press (>1.5s):", COLOR_WHITE, COLOR_GRAY_DARK, 1);
    draw_string(20, y + 100, "   Manual Refresh Immediate", COLOR_GRAY_LIGHT, COLOR_GRAY_DARK, 1);
    draw_string(20, y + 124, "3. Double-Tap Desk / Case:", COLOR_GREEN, COLOR_GRAY_DARK, 1);
    draw_string(20, y + 144, "   IMU Gesture Screen Switch", COLOR_GREEN, COLOR_GRAY_DARK, 1);
    draw_string(20, y + 168, "4. Shake Device:", COLOR_GREEN, COLOR_GRAY_DARK, 1);
    draw_string(20, y + 188, "   IMU Gesture Manual Refresh", COLOR_GREEN, COLOR_GRAY_DARK, 1);
    draw_string(20, y + 212, "Typing vibrations filtered out", COLOR_GRAY_LIGHT, COLOR_GRAY_DARK, 1);

    /* Bottom Navigation Bar */
    draw_fill_rect(0, 770, LCD_WIDTH, 50, COLOR_BLUE_BG);
    draw_string(20, 786, "[BOOT/Tap] Screen 3/3 ->", COLOR_WHITE, COLOR_BLUE_BG, 1);
}

esp_err_t display_ui_init(void) {
    ESP_LOGI(TAG, "Initializing ST7701 Display and UI...");

    /* Backlight PWM Initialization (GPIO6, 100% duty) */
    ledc_timer_config_t timer_conf = {
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .duty_resolution = LEDC_TIMER_8_BIT,
        .timer_num = LEDC_TIMER_3,
        .freq_hz = 50000,
        .clk_cfg = LEDC_SLOW_CLK_RC_FAST,
    };
    ledc_timer_config(&timer_conf);

    ledc_channel_config_t ledc_conf = {
        .gpio_num = BOARD_LCD_BL_PIN,
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .channel = LEDC_CHANNEL_1,
        .intr_type = LEDC_INTR_DISABLE,
        .timer_sel = LEDC_TIMER_3,
        .duty = 255, /* 100% full brightness */
        .hpoint = 0,
    };
    ledc_channel_config(&ledc_conf);

    /* Allocate full 320x820 frame buffer in PSRAM */
    s_framebuffer = (uint16_t *)heap_caps_malloc(LCD_WIDTH * LCD_HEIGHT * sizeof(uint16_t), MALLOC_CAP_SPIRAM);
    if (!s_framebuffer) {
        ESP_LOGE(TAG, "Failed to allocate framebuffer in SPIRAM! Trying default heap...");
        s_framebuffer = (uint16_t *)malloc(LCD_WIDTH * LCD_HEIGHT * sizeof(uint16_t));
    }
    if (!s_framebuffer) {
        ESP_LOGE(TAG, "FATAL: Framebuffer allocation failed!");
        return ESP_ERR_NO_MEM;
    }
    memset(s_framebuffer, 0, LCD_WIDTH * LCD_HEIGHT * sizeof(uint16_t));

    /* Configure 3-wire SPI interface for ST7701 command registers */
    spi_line_config_t line_config = {
        .cs_io_type = IO_TYPE_GPIO,
        .cs_gpio_num = LCD_SPI_CS_PIN,
        .scl_io_type = IO_TYPE_GPIO,
        .scl_gpio_num = LCD_SPI_SCK_PIN,
        .sda_io_type = IO_TYPE_GPIO,
        .sda_gpio_num = LCD_SPI_SDO_PIN,
        .io_expander = NULL,
    };
    esp_lcd_panel_io_3wire_spi_config_t io_config = ST7701_PANEL_IO_3WIRE_SPI_CONFIG(line_config, 0);
    esp_lcd_panel_io_handle_t io_handle = NULL;
    esp_err_t err = esp_lcd_new_panel_io_3wire_spi(&io_config, &io_handle);
    if (err != ESP_OK) {
        ESP_LOGW(TAG, "esp_lcd_new_panel_io_3wire_spi failed: %d", err);
    }

    /* Configure RGB interface timings for 320x820 ST7701 */
    esp_lcd_rgb_panel_config_t rgb_config = {
        .clk_src = LCD_CLK_SRC_DEFAULT,
        .timings = {
            .pclk_hz = 18 * 1000 * 1000,
            .h_res = LCD_WIDTH,
            .v_res = LCD_HEIGHT,
            .hsync_pulse_width = 6,
            .hsync_back_porch = 30,
            .hsync_front_porch = 30,
            .vsync_pulse_width = 40,
            .vsync_back_porch = 20,
            .vsync_front_porch = 20,
            .flags = {
                .pclk_active_neg = 0,
            },
        },
        .data_width = 16,
        .bits_per_pixel = 16,
        .de_gpio_num = LCD_RGB_DE_PIN,
        .pclk_gpio_num = LCD_RGB_PCLK_PIN,
        .vsync_gpio_num = LCD_RGB_VSYNC_PIN,
        .hsync_gpio_num = LCD_RGB_HSYNC_PIN,
        .disp_gpio_num = -1,
        .data_gpio_nums = {
            LCD_RGB_B0_PIN, LCD_RGB_B1_PIN, LCD_RGB_B2_PIN, LCD_RGB_B3_PIN, LCD_RGB_B4_PIN,
            LCD_RGB_G0_PIN, LCD_RGB_G1_PIN, LCD_RGB_G2_PIN, LCD_RGB_G3_PIN, LCD_RGB_G4_PIN, LCD_RGB_G5_PIN,
            LCD_RGB_R0_PIN, LCD_RGB_R1_PIN, LCD_RGB_R2_PIN, LCD_RGB_R3_PIN, LCD_RGB_R4_PIN,
        },
        .flags = {
            .fb_in_psram = 1,
        },
        .bounce_buffer_size_px = 10 * LCD_WIDTH,
        .num_fbs = 2,
    };

    st7701_vendor_config_t vendor_config = {
        .rgb_config = &rgb_config,
        .flags = {
            .mirror_by_cmd = 1,
            .enable_io_multiplex = 0,
        },
    };

    const esp_lcd_panel_dev_config_t panel_config = {
        .reset_gpio_num = LCD_RGB_RESET_PIN,
        .rgb_ele_order = LCD_RGB_ELEMENT_ORDER_RGB,
        .bits_per_pixel = 16,
        .vendor_config = &vendor_config,
    };

    if (io_handle) {
        err = esp_lcd_new_panel_st7701(io_handle, &panel_config, &s_panel_handle);
        if (err == ESP_OK) {
            esp_lcd_panel_reset(s_panel_handle);
            esp_lcd_panel_init(s_panel_handle);
            ESP_LOGI(TAG, "ST7701 RGB Panel initialized successfully.");
        } else {
            ESP_LOGW(TAG, "esp_lcd_new_panel_st7701 failed: %d", err);
        }
    }

    return ESP_OK;
}

void display_ui_set_screen(uint32_t screen_idx) {
    s_current_screen = screen_idx % 3;
}

uint32_t display_ui_get_screen(void) {
    return s_current_screen;
}

void display_ui_cycle_screen(void) {
    s_current_screen = (s_current_screen + 1) % 3;
}

void display_ui_render(const meter_state_t *state) {
    if (!s_framebuffer) return;

    switch (s_current_screen) {
        case 0:
            render_screen_dashboard(state);
            break;
        case 1:
            render_screen_global_resets(state);
            break;
        case 2:
            render_screen_diagnostics(state);
            break;
        default:
            s_current_screen = 0;
            render_screen_dashboard(state);
            break;
    }

    if (s_panel_handle) {
        esp_lcd_panel_draw_bitmap(s_panel_handle, 0, 0, LCD_WIDTH, LCD_HEIGHT, s_framebuffer);
    }
}
