#ifndef METER_GUI_H
#define METER_GUI_H

#include "meter_types.h"
#include "meter_state.h"
#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

#define LCD_LANDSCAPE_WIDTH  820
#define LCD_LANDSCAPE_HEIGHT 320
#define LCD_PORTRAIT_WIDTH   320
#define LCD_PORTRAIT_HEIGHT  820

/* Color palette RGB565 */
#define COLOR_BG            0x0842 /* Very dark navy/slate */
#define COLOR_CARD_BG       0x18C3 /* Dark card background */
#define COLOR_CARD_BORDER   0x2965 /* Border grey */
#define COLOR_TEXT_PRIMARY  0xFFFF /* White */
#define COLOR_TEXT_MUTED    0x9CD3 /* Light grey */
#define COLOR_ACCENT_BLUE   0x04FF /* Bright cyan/blue */
#define COLOR_ACCENT_GREEN  0x07E0 /* Bright green */
#define COLOR_ACCENT_AMBER  0xFD20 /* Amber/orange */
#define COLOR_ACCENT_RED    0xF800 /* Crimson red */
#define COLOR_BAR_BG        0x2104 /* Dark progress track */

typedef struct {
    uint16_t *canvas; /* 820 x 320 RGB565 buffer (524,800 bytes) */
    size_t canvas_size;
} meter_gui_t;

/* Initialize GUI buffer. Caller can provide pre-allocated memory or NULL to malloc. */
bool meter_gui_init(meter_gui_t *gui, uint16_t *external_buffer);
void meter_gui_deinit(meter_gui_t *gui);

/* Render entire GUI based on state and current time */
void meter_gui_render(meter_gui_t *gui, const meter_state_t *state, int64_t now_seconds, uint32_t uptime_ms);

/* Flush 820x320 landscape canvas to 320x820 native portrait panel framebuffer */
void meter_gui_flush_to_native(const meter_gui_t *gui, uint16_t *native_fb, display_orientation_t orientation);

/* Drawing primitives (exposed for host regression testing) */
void gui_clear(meter_gui_t *gui, uint16_t color);
void gui_fill_rect(meter_gui_t *gui, int x, int y, int w, int h, uint16_t color);
void gui_draw_rect(meter_gui_t *gui, int x, int y, int w, int h, uint16_t color);
void gui_draw_char(meter_gui_t *gui, int x, int y, char c, uint16_t color, uint16_t bg, int scale);
void gui_draw_string(meter_gui_t *gui, int x, int y, const char *str, uint16_t color, uint16_t bg, int scale);
void gui_draw_progress_bar(meter_gui_t *gui, int x, int y, int w, int h, double percent, uint16_t fill_color, uint16_t bg_color);

#ifdef __cplusplus
}
#endif

#endif /* METER_GUI_H */
