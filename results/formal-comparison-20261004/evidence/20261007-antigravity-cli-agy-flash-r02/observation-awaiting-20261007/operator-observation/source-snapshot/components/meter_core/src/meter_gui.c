#include "meter_gui.h"
#include "meter_parser.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Simple 8x8 font table for ASCII 32..126 */
static const uint8_t font8x8_basic[95][8] = {
    {0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00}, /* ' ' */
    {0x18,0x3C,0x3C,0x18,0x18,0x00,0x18,0x00}, /* '!' */
    {0x66,0x66,0x24,0x00,0x00,0x00,0x00,0x00}, /* '"' */
    {0x6C,0x6C,0xFE,0x6C,0xFE,0x6C,0x6C,0x00}, /* '#' */
    {0x18,0x3E,0x60,0x3C,0x06,0x7C,0x18,0x00}, /* '$' */
    {0x00,0xC6,0xCC,0x18,0x30,0x66,0xC6,0x00}, /* '%' */
    {0x38,0x6C,0x38,0x76,0xDC,0xCC,0x76,0x00}, /* '&' */
    {0x18,0x18,0x30,0x00,0x00,0x00,0x00,0x00}, /* ''' */
    {0x0C,0x18,0x30,0x30,0x30,0x18,0x0C,0x00}, /* '(' */
    {0x30,0x18,0x0C,0x0C,0x0C,0x18,0x30,0x00}, /* ')' */
    {0x00,0x66,0x3C,0xFF,0x3C,0x66,0x00,0x00}, /* '*' */
    {0x00,0x18,0x18,0x7E,0x18,0x18,0x00,0x00}, /* '+' */
    {0x00,0x00,0x00,0x00,0x00,0x18,0x18,0x30}, /* ',' */
    {0x00,0x00,0x00,0x7E,0x00,0x00,0x00,0x00}, /* '-' */
    {0x00,0x00,0x00,0x00,0x00,0x18,0x18,0x00}, /* '.' */
    {0x06,0x0C,0x18,0x30,0x60,0xC0,0x80,0x00}, /* '/' */
    {0x3C,0x66,0x6E,0x76,0x66,0x66,0x3C,0x00}, /* '0' */
    {0x18,0x38,0x18,0x18,0x18,0x18,0x7E,0x00}, /* '1' */
    {0x3C,0x66,0x06,0x0C,0x18,0x30,0x7E,0x00}, /* '2' */
    {0x3C,0x66,0x06,0x1C,0x06,0x66,0x3C,0x00}, /* '3' */
    {0x0C,0x1C,0x34,0x64,0x7E,0x04,0x04,0x00}, /* '4' */
    {0x7E,0x60,0x7C,0x06,0x06,0x66,0x3C,0x00}, /* '5' */
    {0x1C,0x30,0x60,0x7C,0x66,0x66,0x3C,0x00}, /* '6' */
    {0x7E,0x06,0x0C,0x18,0x30,0x30,0x30,0x00}, /* '7' */
    {0x3C,0x66,0x66,0x3C,0x66,0x66,0x3C,0x00}, /* '8' */
    {0x3C,0x66,0x66,0x3E,0x06,0x0C,0x38,0x00}, /* '9' */
    {0x00,0x18,0x18,0x00,0x00,0x18,0x18,0x00}, /* ':' */
    {0x00,0x18,0x18,0x00,0x00,0x18,0x18,0x30}, /* ';' */
    {0x0C,0x18,0x30,0x60,0x30,0x18,0x0C,0x00}, /* '<' */
    {0x00,0x00,0x7E,0x00,0x7E,0x00,0x00,0x00}, /* '=' */
    {0x30,0x18,0x0C,0x06,0x0C,0x18,0x30,0x00}, /* '>' */
    {0x3C,0x66,0x06,0x0C,0x18,0x00,0x18,0x00}, /* '?' */
    {0x3C,0x66,0x6E,0x6E,0x60,0x62,0x3C,0x00}, /* '@' */
    {0x18,0x3C,0x66,0x66,0x7E,0x66,0x66,0x00}, /* 'A' */
    {0x7C,0x66,0x66,0x7C,0x66,0x66,0x7C,0x00}, /* 'B' */
    {0x3C,0x66,0x60,0x60,0x60,0x66,0x3C,0x00}, /* 'C' */
    {0x78,0x6C,0x66,0x66,0x66,0x6C,0x78,0x00}, /* 'D' */
    {0x7E,0x60,0x60,0x7C,0x60,0x60,0x7E,0x00}, /* 'E' */
    {0x7E,0x60,0x60,0x7C,0x60,0x60,0x60,0x00}, /* 'F' */
    {0x3C,0x66,0x60,0x6E,0x66,0x66,0x3C,0x00}, /* 'G' */
    {0x66,0x66,0x66,0x7E,0x66,0x66,0x66,0x00}, /* 'H' */
    {0x7E,0x18,0x18,0x18,0x18,0x18,0x7E,0x00}, /* 'I' */
    {0x06,0x06,0x06,0x06,0x06,0x66,0x3C,0x00}, /* 'J' */
    {0x66,0x6C,0x78,0x70,0x78,0x6C,0x66,0x00}, /* 'K' */
    {0x60,0x60,0x60,0x60,0x60,0x60,0x7E,0x00}, /* 'L' */
    {0x63,0x77,0x7F,0x6B,0x63,0x63,0x63,0x00}, /* 'M' */
    {0x66,0x76,0x7E,0x7E,0x6E,0x66,0x66,0x00}, /* 'N' */
    {0x3C,0x66,0x66,0x66,0x66,0x66,0x3C,0x00}, /* 'O' */
    {0x7C,0x66,0x66,0x7C,0x60,0x60,0x60,0x00}, /* 'P' */
    {0x3C,0x66,0x66,0x66,0x6A,0x6C,0x36,0x00}, /* 'Q' */
    {0x7C,0x66,0x66,0x7C,0x6C,0x66,0x66,0x00}, /* 'R' */
    {0x3C,0x66,0x60,0x3C,0x06,0x66,0x3C,0x00}, /* 'S' */
    {0x7E,0x18,0x18,0x18,0x18,0x18,0x18,0x00}, /* 'T' */
    {0x66,0x66,0x66,0x66,0x66,0x66,0x3C,0x00}, /* 'U' */
    {0x66,0x66,0x66,0x66,0x66,0x3C,0x18,0x00}, /* 'V' */
    {0x63,0x63,0x63,0x6B,0x7F,0x77,0x63,0x00}, /* 'W' */
    {0x66,0x66,0x3C,0x18,0x3C,0x66,0x66,0x00}, /* 'X' */
    {0x66,0x66,0x66,0x3C,0x18,0x18,0x18,0x00}, /* 'Y' */
    {0x7E,0x06,0x0C,0x18,0x30,0x60,0x7E,0x00}, /* 'Z' */
    {0x3C,0x30,0x30,0x30,0x30,0x30,0x3C,0x00}, /* '[' */
    {0xC0,0x60,0x30,0x18,0x0C,0x06,0x02,0x00}, /* '\' */
    {0x3C,0x0C,0x0C,0x0C,0x0C,0x0C,0x3C,0x00}, /* ']' */
    {0x10,0x38,0x6C,0xC6,0x00,0x00,0x00,0x00}, /* '^' */
    {0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xFF}, /* '_' */
    {0x30,0x18,0x0C,0x00,0x00,0x00,0x00,0x00}, /* '`' */
    {0x00,0x00,0x3C,0x06,0x3E,0x66,0x3E,0x00}, /* 'a' */
    {0x60,0x60,0x7C,0x66,0x66,0x66,0x7C,0x00}, /* 'b' */
    {0x00,0x00,0x3C,0x66,0x60,0x66,0x3C,0x00}, /* 'c' */
    {0x06,0x06,0x3E,0x66,0x66,0x66,0x3E,0x00}, /* 'd' */
    {0x00,0x00,0x3C,0x66,0x7E,0x60,0x3C,0x00}, /* 'e' */
    {0x0E,0x18,0x7C,0x18,0x18,0x18,0x18,0x00}, /* 'f' */
    {0x00,0x00,0x3E,0x66,0x66,0x3E,0x06,0x3C}, /* 'g' */
    {0x60,0x60,0x7C,0x66,0x66,0x66,0x66,0x00}, /* 'h' */
    {0x18,0x00,0x38,0x18,0x18,0x18,0x3C,0x00}, /* 'i' */
    {0x06,0x00,0x0E,0x06,0x06,0x66,0x3C,0x00}, /* 'j' */
    {0x60,0x60,0x66,0x6C,0x78,0x6C,0x66,0x00}, /* 'k' */
    {0x38,0x18,0x18,0x18,0x18,0x18,0x3C,0x00}, /* 'l' */
    {0x00,0x00,0x66,0x7F,0x7F,0x6B,0x63,0x00}, /* 'm' */
    {0x00,0x00,0x7C,0x66,0x66,0x66,0x66,0x00}, /* 'n' */
    {0x00,0x00,0x3C,0x66,0x66,0x66,0x3C,0x00}, /* 'o' */
    {0x00,0x00,0x7C,0x66,0x66,0x7C,0x60,0x60}, /* 'p' */
    {0x00,0x00,0x3E,0x66,0x66,0x3E,0x06,0x06}, /* 'q' */
    {0x00,0x00,0x7C,0x66,0x60,0x60,0x60,0x00}, /* 'r' */
    {0x00,0x00,0x3E,0x60,0x3C,0x06,0x7C,0x00}, /* 's' */
    {0x18,0x18,0x7E,0x18,0x18,0x18,0x0E,0x00}, /* 't' */
    {0x00,0x00,0x66,0x66,0x66,0x66,0x3E,0x00}, /* 'u' */
    {0x00,0x00,0x66,0x66,0x66,0x3C,0x18,0x00}, /* 'v' */
    {0x00,0x00,0x63,0x6B,0x7F,0x3E,0x36,0x00}, /* 'w' */
    {0x00,0x00,0x66,0x3C,0x18,0x3C,0x66,0x00}, /* 'x' */
    {0x00,0x00,0x66,0x66,0x66,0x3E,0x06,0x3C}, /* 'y' */
    {0x00,0x00,0x7E,0x0C,0x18,0x30,0x7E,0x00}, /* 'z' */
    {0x0E,0x18,0x18,0x70,0x18,0x18,0x0E,0x00}, /* '{' */
    {0x18,0x18,0x18,0x00,0x18,0x18,0x18,0x00}, /* '|' */
    {0x70,0x18,0x18,0x0E,0x18,0x18,0x70,0x00}, /* '}' */
    {0x76,0xDC,0x00,0x00,0x00,0x00,0x00,0x00}  /* '~' */
};

bool meter_gui_init(meter_gui_t *gui, uint16_t *external_buffer)
{
    if (!gui) return false;
    gui->canvas_size = LCD_LANDSCAPE_WIDTH * LCD_LANDSCAPE_HEIGHT * sizeof(uint16_t);
    if (external_buffer) {
        gui->canvas = external_buffer;
    } else {
        gui->canvas = (uint16_t *)malloc(gui->canvas_size);
        if (!gui->canvas) return false;
    }
    gui_clear(gui, COLOR_BG);
    return true;
}

void meter_gui_deinit(meter_gui_t *gui)
{
    if (gui && gui->canvas) {
        free(gui->canvas);
        gui->canvas = NULL;
    }
}

void gui_clear(meter_gui_t *gui, uint16_t color)
{
    if (!gui || !gui->canvas) return;
    size_t total = LCD_LANDSCAPE_WIDTH * LCD_LANDSCAPE_HEIGHT;
    for (size_t i = 0; i < total; ++i) {
        gui->canvas[i] = color;
    }
}

void gui_fill_rect(meter_gui_t *gui, int x, int y, int w, int h, uint16_t color)
{
    if (!gui || !gui->canvas || w <= 0 || h <= 0) return;
    int x0 = x < 0 ? 0 : x;
    int y0 = y < 0 ? 0 : y;
    int x1 = (x + w) > LCD_LANDSCAPE_WIDTH ? LCD_LANDSCAPE_WIDTH : (x + w);
    int y1 = (y + h) > LCD_LANDSCAPE_HEIGHT ? LCD_LANDSCAPE_HEIGHT : (y + h);

    for (int py = y0; py < y1; ++py) {
        uint16_t *row = &gui->canvas[py * LCD_LANDSCAPE_WIDTH];
        for (int px = x0; px < x1; ++px) {
            row[px] = color;
        }
    }
}

void gui_draw_rect(meter_gui_t *gui, int x, int y, int w, int h, uint16_t color)
{
    if (!gui || !gui->canvas || w <= 0 || h <= 0) return;
    gui_fill_rect(gui, x, y, w, 1, color);
    gui_fill_rect(gui, x, y + h - 1, w, 1, color);
    gui_fill_rect(gui, x, y, 1, h, color);
    gui_fill_rect(gui, x + w - 1, y, 1, h, color);
}

void gui_draw_char(meter_gui_t *gui, int x, int y, char c, uint16_t color, uint16_t bg, int scale)
{
    if (!gui || !gui->canvas) return;
    if (c < 32 || c > 126) c = ' ';
    const uint8_t *bitmap = font8x8_basic[c - 32];

    for (int row = 0; row < 8; ++row) {
        uint8_t bits = bitmap[row];
        for (int col = 0; col < 8; ++col) {
            uint16_t pcolor = (bits & (0x80 >> col)) ? color : bg;
            if (pcolor == 0 && bg == 0) continue; /* Transparent background */
            if (scale == 1) {
                int px = x + col;
                int py = y + row;
                if (px >= 0 && px < LCD_LANDSCAPE_WIDTH && py >= 0 && py < LCD_LANDSCAPE_HEIGHT) {
                    gui->canvas[py * LCD_LANDSCAPE_WIDTH + px] = pcolor;
                }
            } else {
                gui_fill_rect(gui, x + col * scale, y + row * scale, scale, scale, pcolor);
            }
        }
    }
}

void gui_draw_string(meter_gui_t *gui, int x, int y, const char *str, uint16_t color, uint16_t bg, int scale)
{
    if (!gui || !str) return;
    int cur_x = x;
    int step = 8 * scale;
    while (*str) {
        if (*str == '\n') {
            cur_x = x;
            y += 10 * scale;
        } else {
            if (cur_x + step <= LCD_LANDSCAPE_WIDTH) {
                gui_draw_char(gui, cur_x, y, *str, color, bg, scale);
            }
            cur_x += step;
        }
        str++;
    }
}

void gui_draw_progress_bar(meter_gui_t *gui, int x, int y, int w, int h, double percent, uint16_t fill_color, uint16_t bg_color)
{
    gui_fill_rect(gui, x, y, w, h, bg_color);
    gui_draw_rect(gui, x, y, w, h, COLOR_CARD_BORDER);
    if (percent < 0.0) percent = 0.0;
    if (percent > 100.0) percent = 100.0;
    int fill_w = (int)((w - 4) * (percent / 100.0));
    if (fill_w > 0) {
        gui_fill_rect(gui, x + 2, y + 2, fill_w, h - 4, fill_color);
    }
}

static void render_header(meter_gui_t *gui, const char *title, screen_mode_t mode, bool is_stale, const char *time_str)
{
    gui_fill_rect(gui, 0, 0, LCD_LANDSCAPE_WIDTH, 36, 0x0185);
    gui_draw_string(gui, 16, 10, title, COLOR_TEXT_PRIMARY, 0, 2);

    /* Screen navigation pills */
    const char *names[3] = {"1:DASHBOARD", "2:RESETS", "3:STATUS"};
    int pill_x = 420;
    for (int i = 0; i < 3; ++i) {
        uint16_t pbg = (i == (int)mode) ? COLOR_ACCENT_BLUE : COLOR_CARD_BG;
        uint16_t ptc = (i == (int)mode) ? 0x0000 : COLOR_TEXT_MUTED;
        gui_fill_rect(gui, pill_x, 6, 105, 24, pbg);
        gui_draw_rect(gui, pill_x, 6, 105, 24, COLOR_CARD_BORDER);
        gui_draw_string(gui, pill_x + 6, 12, names[i], ptc, 0, 1);
        pill_x += 112;
    }

    /* Stale indicator */
    if (is_stale) {
        gui_fill_rect(gui, 755, 6, 52, 24, COLOR_ACCENT_AMBER);
        gui_draw_string(gui, 760, 12, "STALE", 0x0000, 0, 1);
    } else {
        gui_fill_rect(gui, 755, 6, 52, 24, COLOR_ACCENT_GREEN);
        gui_draw_string(gui, 765, 12, "LIVE", 0x0000, 0, 1);
    }
}

static void render_footer(meter_gui_t *gui, display_orientation_t orient)
{
    gui_fill_rect(gui, 0, 298, LCD_LANDSCAPE_WIDTH, 22, 0x0185);
    char buf[128];
    snprintf(buf, sizeof(buf), "BOOT: SWITCH SCREEN | ORIENT: %s | TRANSPORT: USB Serial / JTAG 115200 8N1",
             (orient == ORIENTATION_LANDSCAPE_NORMAL) ? "0 DEG" : "180 DEG");
    gui_draw_string(gui, 16, 304, buf, COLOR_TEXT_MUTED, 0, 1);
}

static void render_dashboard(meter_gui_t *gui, const meter_state_t *state, int64_t now_sec)
{
    render_header(gui, "CODEX METER", SCREEN_DASHBOARD, state->is_stale, state->last_receive_stamp);

    if (state->usage_count == 0) {
        /* No data yet */
        gui_fill_rect(gui, 40, 60, 740, 215, COLOR_CARD_BG);
        gui_draw_rect(gui, 40, 60, 740, 215, COLOR_CARD_BORDER);
        gui_draw_string(gui, 260, 130, "WAITING FOR USB DATA...", COLOR_ACCENT_BLUE, 0, 2);
        gui_draw_string(gui, 230, 170, "Connect host sender to stream cdm/1 frames", COLOR_TEXT_MUTED, 0, 1);
        render_footer(gui, state->orientation);
        return;
    }

    /* Render usage cards */
    int card_w;
    if (state->usage_count == 1) {
        card_w = LCD_LANDSCAPE_WIDTH - 32; /* 788 px for single full-width card */
    } else {
        card_w = (LCD_LANDSCAPE_WIDTH - 32 - (int)(state->usage_count - 1) * 12) / (int)state->usage_count;
        if (card_w < 220) card_w = 220;
        if (card_w > 380) card_w = 380;
    }

    int card_x = 16;
    for (size_t i = 0; i < state->usage_count && i < 3; ++i) {
        const meter_snapshot_t *snap = &state->usage[i];
        gui_fill_rect(gui, card_x, 46, card_w, 242, COLOR_CARD_BG);
        gui_draw_rect(gui, card_x, 46, card_w, 242, COLOR_CARD_BORDER);

        /* Provider title banner */
        char title_buf[128];
        snprintf(title_buf, sizeof(title_buf), "%s", snap->provider_id);
        gui_draw_string(gui, card_x + 12, 56, title_buf, COLOR_TEXT_PRIMARY, 0, 2);

        char sub_buf[160];
        snprintf(sub_buf, sizeof(sub_buf), "%s / %s", snap->agent_id, snap->host_id);
        gui_draw_string(gui, card_x + 12, 78, sub_buf, COLOR_TEXT_MUTED, 0, 1);

        /* Card status pill */
        const char *st_text = (snap->status == SNAPSHOT_STATUS_AVAILABLE) ? "OK" :
                              (snap->status == SNAPSHOT_STATUS_STALE) ? "STALE" :
                              (snap->status == SNAPSHOT_STATUS_UNSUPPORTED) ? "UNSUPPORTED" : "ERROR";
        uint16_t st_color = (snap->status == SNAPSHOT_STATUS_AVAILABLE) ? COLOR_ACCENT_GREEN :
                            (snap->status == SNAPSHOT_STATUS_STALE) ? COLOR_ACCENT_AMBER : COLOR_ACCENT_RED;
        gui_fill_rect(gui, card_x + card_w - 95, 54, 85, 20, st_color);
        gui_draw_string(gui, card_x + card_w - 90, 60, st_text, 0x0000, 0, 1);

        /* Windows */
        int win_y = 100;
        int win_step = (snap->window_count <= 2) ? 74 : 64;
        for (size_t w = 0; w < snap->window_count && w < 2; ++w) {
            const meter_window_t *win = &snap->windows[w];
            const char *wtitle = (win->label[0] != '\0') ? win->label : win->window_id;

            char wlbl[128];
            if (win->has_percent) {
                snprintf(wlbl, sizeof(wlbl), "%s: %.0f%% REMAINING", wtitle, win->percent_remaining);
            } else {
                snprintf(wlbl, sizeof(wlbl), "%s", wtitle);
            }
            /* Prominent header in scale 2 for card_w > 400 (single card) */
            gui_draw_string(gui, card_x + 12, win_y, wlbl, COLOR_TEXT_PRIMARY, 0, (card_w > 400) ? 2 : 1);

            double pct = win->has_percent ? win->percent_used :
                         (win->has_absolute && win->limit_units > 0) ? (win->used_units / win->limit_units * 100.0) : 0.0;

            uint16_t bar_color = (pct > 90.0) ? COLOR_ACCENT_RED : (pct > 75.0) ? COLOR_ACCENT_AMBER : COLOR_ACCENT_GREEN;
            gui_draw_progress_bar(gui, card_x + 12, win_y + 22, card_w - 24, 18, pct, bar_color, COLOR_BAR_BG);

            char detail_buf[256];
            if (win->has_percent) {
                snprintf(detail_buf, sizeof(detail_buf), "Used: %.0f%% | Remaining: %.0f%% | Status: %s",
                         win->percent_used, win->percent_remaining, (snap->status == SNAPSHOT_STATUS_STALE) ? "STALE" : "LIVE");
            } else if (win->has_absolute) {
                snprintf(detail_buf, sizeof(detail_buf), "%.0f / %.0f %s (%.0f%% remaining)",
                         win->used_units, win->limit_units, (win->unit == UNIT_TOKEN) ? "TOKENS" : "CREDITS", 100.0 - pct);
            } else {
                snprintf(detail_buf, sizeof(detail_buf), "Used: %.1f%%", pct);
            }
            gui_draw_string(gui, card_x + 12, win_y + 45, detail_buf, COLOR_TEXT_MUTED, 0, 1);
            win_y += win_step;
        }

        /* Observed timestamp & provenance */
        char obs_buf[256] = {0};
        if (snap->observed_at[0] != '\0') {
            snprintf(obs_buf, sizeof(obs_buf), "PROVENANCE: %s | OBSERVED: %s | STATUS: %s",
                     snap->source_kind, snap->observed_at, (snap->stale) ? "STALE" : "LIVE");
        } else {
            snprintf(obs_buf, sizeof(obs_buf), "PROVENANCE: %s | STATUS: %s",
                     snap->source_kind, (snap->stale) ? "STALE" : "LIVE");
        }
        gui_draw_string(gui, card_x + 12, 266, obs_buf, COLOR_TEXT_MUTED, 0, 1);

        card_x += card_w + 12;
    }

    render_footer(gui, state->orientation);
}

static void render_global_resets(meter_gui_t *gui, const meter_state_t *state, int64_t now_sec)
{
    render_header(gui, "GLOBAL RESETS", SCREEN_GLOBAL_RESETS, state->is_stale, state->last_receive_stamp);

    /* Left main card: Latest Reset */
    gui_fill_rect(gui, 16, 46, 480, 242, COLOR_CARD_BG);
    gui_draw_rect(gui, 16, 46, 480, 242, COLOR_CARD_BORDER);

    gui_draw_string(gui, 32, 60, "SOURCE: codex-resets.com", COLOR_ACCENT_BLUE, 0, 1);
    gui_draw_string(gui, 32, 80, "LATEST GLOBAL RESET", COLOR_TEXT_PRIMARY, 0, 2);

    /* Prefer codex-resets.com source per contract */
    const meter_global_reset_t *gr = NULL;
    for (size_t i = 0; i < state->global_reset_count; ++i) {
        if (strcmp(state->global_resets[i].source, "codex-resets.com") == 0) {
            gr = &state->global_resets[i];
            break;
        }
    }
    if (!gr && state->global_reset_count > 0) {
        gr = &state->global_resets[0];
    }

    if (gr && gr->latest_reset_at[0] != '\0') {
        char time_buf[128];
        snprintf(time_buf, sizeof(time_buf), "RESET AT: %s", gr->latest_reset_at);
        gui_draw_string(gui, 32, 115, time_buf, COLOR_ACCENT_GREEN, 0, 2);

        int64_t rsec = 0;
        if (meter_parse_rfc3339(gr->latest_reset_at, &rsec) && now_sec >= rsec) {
            int64_t elapsed = now_sec - rsec;
            int hours = (int)(elapsed / 3600);
            int mins = (int)((elapsed % 3600) / 60);
            char el_buf[128];
            snprintf(el_buf, sizeof(el_buf), "ELAPSED: %d hours %d minutes ago", hours, mins);
            gui_draw_string(gui, 32, 145, el_buf, COLOR_TEXT_PRIMARY, 0, 1);
        }

        if (gr->has_forecast_24h) {
            gui_draw_string(gui, 32, 175, "NEXT 24H FORECAST PROBABILITY", COLOR_TEXT_MUTED, 0, 1);
            gui_draw_progress_bar(gui, 32, 195, 430, 20, gr->forecast_24h_percent, COLOR_ACCENT_BLUE, COLOR_BAR_BG);
            char fbuf[32];
            snprintf(fbuf, sizeof(fbuf), "%.1f%%", gr->forecast_24h_percent);
            gui_draw_string(gui, 32, 222, fbuf, COLOR_TEXT_PRIMARY, 0, 1);
        }
    } else {
        /* Default baseline screen */
        gui_draw_string(gui, 32, 120, "NO RECENT RESET RECORD", COLOR_TEXT_MUTED, 0, 2);
        gui_draw_string(gui, 32, 160, "Status: Monitoring codex-resets.com", COLOR_TEXT_MUTED, 0, 1);
        gui_draw_string(gui, 32, 185, "Awaiting global reset schedule announcement", COLOR_TEXT_MUTED, 0, 1);
    }


    /* Right side card: Source details */
    gui_fill_rect(gui, 508, 46, 296, 242, COLOR_CARD_BG);
    gui_draw_rect(gui, 508, 46, 296, 242, COLOR_CARD_BORDER);

    gui_draw_string(gui, 524, 60, "SOURCE DETAILS", COLOR_TEXT_PRIMARY, 0, 2);
    gui_draw_string(gui, 524, 90, "Provider: codex-resets.com", COLOR_TEXT_MUTED, 0, 1);

    if (gr && gr->captured_at[0] != '\0') {
        char cap_buf[128];
        snprintf(cap_buf, sizeof(cap_buf), "Captured: %s", gr->captured_at);
        gui_draw_string(gui, 524, 115, cap_buf, COLOR_TEXT_MUTED, 0, 1);
    }

    gui_draw_string(gui, 524, 145, "Source Separation:", COLOR_TEXT_MUTED, 0, 1);
    gui_draw_string(gui, 524, 165, "codex-reset.com  (Forecast Only)", COLOR_TEXT_MUTED, 0, 1);
    gui_draw_string(gui, 524, 185, "codex-resets.com (Historical)", COLOR_ACCENT_GREEN, 0, 1);

    gui_draw_string(gui, 524, 220, "Stale Threshold: 300s", COLOR_TEXT_MUTED, 0, 1);
    gui_draw_string(gui, 524, 245, state->is_stale ? "Status: STALE" : "Status: FRESH",
                    state->is_stale ? COLOR_ACCENT_AMBER : COLOR_ACCENT_GREEN, 0, 1);

    render_footer(gui, state->orientation);
}

static void render_status_error(meter_gui_t *gui, const meter_state_t *state, int64_t now_sec, uint32_t uptime_ms)
{
    render_header(gui, "SYSTEM STATUS", SCREEN_STATUS_ERROR, state->is_stale, state->last_receive_stamp);

    int col_w = 250;
    /* Col 1: Transport */
    gui_fill_rect(gui, 16, 46, col_w, 242, COLOR_CARD_BG);
    gui_draw_rect(gui, 16, 46, col_w, 242, COLOR_CARD_BORDER);
    gui_draw_string(gui, 28, 58, "USB TRANSPORT", COLOR_ACCENT_BLUE, 0, 2);
    gui_draw_string(gui, 28, 88, "Protocol: cdm/1", COLOR_TEXT_PRIMARY, 0, 1);
    gui_draw_string(gui, 28, 108, "Baud: 115200 8N1", COLOR_TEXT_MUTED, 0, 1);

    char seq_buf[64];
    if (state->has_sequence) {
        snprintf(seq_buf, sizeof(seq_buf), "Sequence: %u", (unsigned int)state->current_sequence);
    } else {
        snprintf(seq_buf, sizeof(seq_buf), "Sequence: NONE");
    }
    gui_draw_string(gui, 28, 132, seq_buf, COLOR_TEXT_PRIMARY, 0, 1);

    if (state->last_receive_time > 0) {
        int64_t age = now_sec - state->last_receive_time;
        char age_buf[64];
        snprintf(age_buf, sizeof(age_buf), "Age: %llds", (long long)age);
        gui_draw_string(gui, 28, 156, age_buf, COLOR_TEXT_MUTED, 0, 1);
    }

    gui_draw_string(gui, 28, 185, "Integrity: CRC-32", COLOR_TEXT_MUTED, 0, 1);
    gui_draw_string(gui, 28, 205, "Enforce Canonical: ON", COLOR_TEXT_MUTED, 0, 1);

    /* Col 2: Cache & Error */
    gui_fill_rect(gui, 280, 46, col_w, 242, COLOR_CARD_BG);
    gui_draw_rect(gui, 280, 46, col_w, 242, COLOR_CARD_BORDER);
    gui_draw_string(gui, 292, 58, "CACHE / RECOVERY", COLOR_ACCENT_BLUE, 0, 2);

    char csnap_buf[64], cres_buf[64];
    snprintf(csnap_buf, sizeof(csnap_buf), "Cached Snapshots: %u", (unsigned int)state->usage_count);
    snprintf(cres_buf, sizeof(cres_buf), "Cached Resets: %u", (unsigned int)state->global_reset_count);
    gui_draw_string(gui, 292, 88, csnap_buf, COLOR_TEXT_PRIMARY, 0, 1);
    gui_draw_string(gui, 292, 108, cres_buf, COLOR_TEXT_PRIMARY, 0, 1);

    gui_draw_string(gui, 292, 135, "HEALTH STATUS:", COLOR_TEXT_MUTED, 0, 1);
    if (state->has_error) {
        gui_fill_rect(gui, 292, 152, col_w - 24, 24, COLOR_ACCENT_RED);
        gui_draw_string(gui, 298, 158, state->last_error_code, 0xFFFF, 0, 1);

        char reas[128];
        snprintf(reas, sizeof(reas), "%.30s", state->last_error_reason);
        gui_draw_string(gui, 292, 184, reas, COLOR_ACCENT_RED, 0, 1);
        gui_draw_string(gui, 292, 204, "Last-Good Preserved", COLOR_ACCENT_GREEN, 0, 1);
    } else {
        gui_fill_rect(gui, 292, 152, col_w - 24, 24, COLOR_ACCENT_GREEN);
        gui_draw_string(gui, 330, 158, "HEALTHY", 0x0000, 0, 1);
        gui_draw_string(gui, 292, 185, "No Active Errors", COLOR_TEXT_MUTED, 0, 1);
        gui_draw_string(gui, 292, 205, "Auto Recovery: READY", COLOR_TEXT_MUTED, 0, 1);
    }

    if (state->last_good_stamp[0] != '\0') {
        char lg_buf[64];
        snprintf(lg_buf, sizeof(lg_buf), "Last Good: %.16s", state->last_good_stamp);
        gui_draw_string(gui, 292, 240, lg_buf, COLOR_TEXT_MUTED, 0, 1);
    }

    /* Col 3: Hardware */
    gui_fill_rect(gui, 544, 46, col_w + 14, 242, COLOR_CARD_BG);
    gui_draw_rect(gui, 544, 46, col_w + 14, 242, COLOR_CARD_BORDER);
    gui_draw_string(gui, 556, 58, "HARDWARE INFO", COLOR_ACCENT_BLUE, 0, 2);
    gui_draw_string(gui, 556, 88, "ESP32-S3R8 / 16MB Flash", COLOR_TEXT_PRIMARY, 0, 1);
    gui_draw_string(gui, 556, 108, "PSRAM: 8MB Octal (80MHz)", COLOR_TEXT_MUTED, 0, 1);
    gui_draw_string(gui, 556, 128, "LCD: 820x320 ST7701 RGB", COLOR_TEXT_MUTED, 0, 1);
    gui_draw_string(gui, 556, 148, "IMU: QMI8658 6-Axis (I2C)", COLOR_TEXT_PRIMARY, 0, 1);

    char ori_buf[48];
    snprintf(ori_buf, sizeof(ori_buf), "Orientation: %s",
             (state->orientation == ORIENTATION_LANDSCAPE_NORMAL) ? "NORMAL (0 DEG)" : "FLIPPED (180 DEG)");
    gui_draw_string(gui, 556, 172, ori_buf, COLOR_ACCENT_GREEN, 0, 1);

    char up_buf[48];
    snprintf(up_buf, sizeof(up_buf), "Uptime: %u sec", (unsigned int)(uptime_ms / 1000));
    gui_draw_string(gui, 556, 200, up_buf, COLOR_TEXT_MUTED, 0, 1);

    gui_draw_string(gui, 556, 230, "Debounce: 300ms BOOT", COLOR_TEXT_MUTED, 0, 1);
    gui_draw_string(gui, 556, 248, "Auto Refresh: <=60s", COLOR_TEXT_MUTED, 0, 1);

    render_footer(gui, state->orientation);
}

void meter_gui_render(meter_gui_t *gui, const meter_state_t *state, int64_t now_seconds, uint32_t uptime_ms)
{
    if (!gui || !state) return;
    gui_clear(gui, COLOR_BG);

    switch (state->screen_mode) {
    case SCREEN_DASHBOARD:
        render_dashboard(gui, state, now_seconds);
        break;
    case SCREEN_GLOBAL_RESETS:
        render_global_resets(gui, state, now_seconds);
        break;
    case SCREEN_STATUS_ERROR:
        render_status_error(gui, state, now_seconds, uptime_ms);
        break;
    default:
        render_dashboard(gui, state, now_seconds);
        break;
    }
}

void meter_gui_flush_to_native(const meter_gui_t *gui, uint16_t *native_fb, display_orientation_t orientation)
{
    if (!gui || !gui->canvas || !native_fb) return;

    /* Native panel: 320 columns wide, 820 rows high.
     * Landscape canvas: 820 columns wide, 320 rows high. */
    if (orientation == ORIENTATION_LANDSCAPE_NORMAL) {
        for (int ly = 0; ly < LCD_LANDSCAPE_HEIGHT; ++ly) {
            const uint16_t *src_row = &gui->canvas[ly * LCD_LANDSCAPE_WIDTH];
            int px = ly;
            for (int lx = 0; lx < LCD_LANDSCAPE_WIDTH; ++lx) {
                int py = 819 - lx;
                native_fb[py * LCD_PORTRAIT_WIDTH + px] = src_row[lx];
            }
        }
    } else {
        /* Inverted landscape (180 deg) */
        for (int ly = 0; ly < LCD_LANDSCAPE_HEIGHT; ++ly) {
            const uint16_t *src_row = &gui->canvas[ly * LCD_LANDSCAPE_WIDTH];
            int px = 319 - ly;
            for (int lx = 0; lx < LCD_LANDSCAPE_WIDTH; ++lx) {
                int py = lx;
                native_fb[py * LCD_PORTRAIT_WIDTH + px] = src_row[lx];
            }
        }
    }
}
