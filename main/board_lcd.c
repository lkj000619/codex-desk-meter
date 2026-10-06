#include "board_lcd.h"

#include "meter_core.h"

#include "driver/gpio.h"
#include "driver/ledc.h"
#include "esp_check.h"
#include "esp_heap_caps.h"
#include "esp_lcd_panel_io_additions.h"
#include "esp_lcd_panel_ops.h"
#include "esp_lcd_panel_rgb.h"
#include "esp_lcd_st7701.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "cJSON.h"

#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define LCD_WIDTH 820
#define LCD_HEIGHT 320
#define FRAME_PIXELS ((size_t)LCD_WIDTH * LCD_HEIGHT)
#define FRAME_BYTES (FRAME_PIXELS * sizeof(uint16_t))
#define PIN_LCD_CS 0
#define PIN_LCD_SCK 2
#define PIN_LCD_SDO 1
#define PIN_LCD_RESET 16
#define PIN_BACKLIGHT 6

static const char *TAG = "meter_lcd";
static esp_lcd_panel_handle_t panel;
static uint16_t *canvas;
static bool ledc_ready;

#define CMD(c, bytes, delay) { (c), (bytes), sizeof(bytes), (delay) }
#define CMD0(c, delay) { (c), NULL, 0, (delay) }

/* ST7701 vendor sequence is from the hash-checked Waveshare 09_FactoryProgram/main/main.cpp. */
static const st7701_lcd_init_cmd_t panel_commands[] = {
    CMD(0xFF, ((uint8_t[]){0x77,0x01,0x00,0x00,0x13}), 0),
    CMD(0xEF, ((uint8_t[]){0x08}), 0),
    CMD(0xFF, ((uint8_t[]){0x77,0x01,0x00,0x00,0x10}), 0),
    CMD(0xC0, ((uint8_t[]){0xE5,0x02}), 0),
    CMD(0xC1, ((uint8_t[]){0x15,0x0A}), 0),
    CMD(0xC2, ((uint8_t[]){0x07,0x02}), 0),
    CMD(0xCC, ((uint8_t[]){0x10}), 0),
    CMD(0xB0, ((uint8_t[]){0x00,0x08,0x51,0x0D,0xCE,0x06,0x00,0x08,0x08,0x24,0x05,0xD0,0x0F,0x6F,0x36,0x1F}), 0),
    CMD(0xB1, ((uint8_t[]){0x00,0x10,0x4F,0x0C,0x11,0x05,0x00,0x07,0x07,0x18,0x02,0xD3,0x11,0x6E,0x34,0x1F}), 0),
    CMD(0xFF, ((uint8_t[]){0x77,0x01,0x00,0x00,0x11}), 0),
    CMD(0xB0, ((uint8_t[]){0x4D}), 0), CMD(0xB1, ((uint8_t[]){0x37}), 0),
    CMD(0xB2, ((uint8_t[]){0x87}), 0), CMD(0xB3, ((uint8_t[]){0x80}), 0),
    CMD(0xB5, ((uint8_t[]){0x4A}), 0), CMD(0xB7, ((uint8_t[]){0x85}), 0),
    CMD(0xB8, ((uint8_t[]){0x21}), 0), CMD(0xB9, ((uint8_t[]){0x00,0x13}), 0),
    CMD(0xC0, ((uint8_t[]){0x09}), 0), CMD(0xC1, ((uint8_t[]){0x78}), 0),
    CMD(0xC2, ((uint8_t[]){0x78}), 0), CMD(0xD0, ((uint8_t[]){0x88}), 0),
    CMD(0xE0, ((uint8_t[]){0x80,0x00,0x02}), 100),
    CMD(0xE1, ((uint8_t[]){0x0F,0xA0,0x00,0x00,0x10,0xA0,0x00,0x00,0x00,0x60,0x60}), 0),
    CMD(0xE2, ((uint8_t[]){0x30,0x30,0x60,0x60,0x45,0xA0,0x00,0x00,0x46,0xA0,0x00,0x00,0x00}), 0),
    CMD(0xE3, ((uint8_t[]){0x00,0x00,0x33,0x33}), 0), CMD(0xE4, ((uint8_t[]){0x44,0x44}), 0),
    CMD(0xE5, ((uint8_t[]){0x0F,0x4A,0xA0,0xA0,0x11,0x4A,0xA0,0xA0,0x13,0x4A,0xA0,0xA0,0x15,0x4A,0xA0,0xA0}), 0),
    CMD(0xE6, ((uint8_t[]){0x00,0x00,0x33,0x33}), 0), CMD(0xE7, ((uint8_t[]){0x44,0x44}), 0),
    CMD(0xE8, ((uint8_t[]){0x10,0x4A,0xA0,0xA0,0x12,0x4A,0xA0,0xA0,0x14,0x4A,0xA0,0xA0,0x16,0x4A,0xA0,0xA0}), 0),
    CMD(0xEB, ((uint8_t[]){0x02,0x00,0x4E,0x4E,0xEE,0x44,0x00}), 0),
    CMD(0xED, ((uint8_t[]){0xFF,0xFF,0x04,0x56,0x72,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0x27,0x65,0x40,0xFF,0xFF}), 0),
    CMD(0xEF, ((uint8_t[]){0x08,0x08,0x08,0x40,0x3F,0x64}), 0),
    CMD(0xFF, ((uint8_t[]){0x77,0x01,0x00,0x00,0x13}), 0), CMD(0xE8, ((uint8_t[]){0x00,0x0E}), 0),
    CMD(0xFF, ((uint8_t[]){0x77,0x01,0x00,0x00,0x00}), 0), CMD0(0x11, 120),
    CMD(0xFF, ((uint8_t[]){0x77,0x01,0x00,0x00,0x13}), 0),
    CMD(0xE8, ((uint8_t[]){0x00,0x0C}), 10), CMD(0xE8, ((uint8_t[]){0x00,0x00}), 0),
    CMD(0xFF, ((uint8_t[]){0x77,0x01,0x00,0x00,0x00}), 0),
    CMD(0x3A, ((uint8_t[]){0x55}), 0),
    /* MV rotates the native 320x820 panel scan to the product's 820x320 landscape surface. */
    CMD(0x36, ((uint8_t[]){0x20}), 0),
    CMD(0x35, ((uint8_t[]){0x00}), 0), CMD0(0x29, 20),
};

#undef CMD
#undef CMD0

static const uint8_t *glyph(char c)
{
    static const uint8_t blank[5] = {0,0,0,0,0};
    static const uint8_t question[5] = {0x02,0x01,0x51,0x09,0x06};
    static const uint8_t digits[10][5] = {
        {0x3E,0x51,0x49,0x45,0x3E},{0x00,0x42,0x7F,0x40,0x00},
        {0x42,0x61,0x51,0x49,0x46},{0x21,0x41,0x45,0x4B,0x31},
        {0x18,0x14,0x12,0x7F,0x10},{0x27,0x45,0x45,0x45,0x39},
        {0x3C,0x4A,0x49,0x49,0x30},{0x01,0x71,0x09,0x05,0x03},
        {0x36,0x49,0x49,0x49,0x36},{0x06,0x49,0x49,0x29,0x1E}
    };
    static const uint8_t alpha[26][5] = {
        {0x7E,0x11,0x11,0x11,0x7E},{0x7F,0x49,0x49,0x49,0x36},
        {0x3E,0x41,0x41,0x41,0x22},{0x7F,0x41,0x41,0x22,0x1C},
        {0x7F,0x49,0x49,0x49,0x41},{0x7F,0x09,0x09,0x09,0x01},
        {0x3E,0x41,0x49,0x49,0x7A},{0x7F,0x08,0x08,0x08,0x7F},
        {0x00,0x41,0x7F,0x41,0x00},{0x20,0x40,0x41,0x3F,0x01},
        {0x7F,0x08,0x14,0x22,0x41},{0x7F,0x40,0x40,0x40,0x40},
        {0x7F,0x02,0x0C,0x02,0x7F},{0x7F,0x04,0x08,0x10,0x7F},
        {0x3E,0x41,0x41,0x41,0x3E},{0x7F,0x09,0x09,0x09,0x06},
        {0x3E,0x41,0x51,0x21,0x5E},{0x7F,0x09,0x19,0x29,0x46},
        {0x46,0x49,0x49,0x49,0x31},{0x01,0x01,0x7F,0x01,0x01},
        {0x3F,0x40,0x40,0x40,0x3F},{0x1F,0x20,0x40,0x20,0x1F},
        {0x3F,0x40,0x38,0x40,0x3F},{0x63,0x14,0x08,0x14,0x63},
        {0x07,0x08,0x70,0x08,0x07},{0x61,0x51,0x49,0x45,0x43}
    };
    static const uint8_t dash[5] = {0x08,0x08,0x08,0x08,0x08};
    static const uint8_t underscore[5] = {0x40,0x40,0x40,0x40,0x40};
    static const uint8_t dot[5] = {0,0x60,0x60,0,0};
    static const uint8_t colon[5] = {0,0x36,0x36,0,0};
    static const uint8_t slash[5] = {0x20,0x10,0x08,0x04,0x02};
    static const uint8_t percent[5] = {0x63,0x13,0x08,0x64,0x63};
    static const uint8_t equals[5] = {0x14,0x14,0x14,0x14,0x14};
    static const uint8_t comma[5] = {0,0x50,0x30,0,0};
    static const uint8_t plus[5] = {0x08,0x08,0x3E,0x08,0x08};
    static const uint8_t question_mark[5] = {0x02,0x01,0x51,0x09,0x06};
    if (c >= 'a' && c <= 'z') c = (char)(c - 'a' + 'A');
    if (c >= '0' && c <= '9') return digits[c - '0'];
    if (c >= 'A' && c <= 'Z') return alpha[c - 'A'];
    switch (c) {
    case ' ': return blank;
    case '-': return dash;
    case '_': return underscore;
    case '.': return dot;
    case ':': return colon;
    case '/': return slash;
    case '%': return percent;
    case '=': return equals;
    case ',': return comma;
    case '+': return plus;
    case '?': return question_mark;
    default: return question;
    }
}

static void clear_canvas(uint16_t color)
{
    for (size_t i = 0; i < FRAME_PIXELS; i++) canvas[i] = color;
}

static void fill_rect(int x, int y, int width, int height, uint16_t color)
{
    if (x < 0) { width += x; x = 0; }
    if (y < 0) { height += y; y = 0; }
    if (x + width > LCD_WIDTH) width = LCD_WIDTH - x;
    if (y + height > LCD_HEIGHT) height = LCD_HEIGHT - y;
    if (width <= 0 || height <= 0) return;
    for (int row = y; row < y + height; row++) {
        uint16_t *target = canvas + (size_t)row * LCD_WIDTH + x;
        for (int col = 0; col < width; col++) target[col] = color;
    }
}

static void draw_text(int x, int y, const char *text, uint16_t color, int scale, int max_chars)
{
    if (!text) return;
    int column = 0;
    while (*text && column < max_chars && x + (column + 1) * 6 * scale <= LCD_WIDTH) {
        const uint8_t *columns = glyph(*text++);
        for (int cx = 0; cx < 5; cx++) {
            for (int cy = 0; cy < 7; cy++) {
                if (columns[cx] & (1u << cy)) fill_rect(x + (column * 6 + cx) * scale,
                                                        y + cy * scale, scale, scale, color);
            }
        }
        column++;
    }
}

static const char *json_string(cJSON *object, const char *name)
{
    cJSON *item = cJSON_GetObjectItemCaseSensitive(object, name);
    return cJSON_IsString(item) ? item->valuestring : NULL;
}

static bool json_number(cJSON *object, const char *name, double *value)
{
    cJSON *item = cJSON_GetObjectItemCaseSensitive(object, name);
    if (!cJSON_IsNumber(item)) return false;
    *value = item->valuedouble;
    return true;
}

static void number_text(char *buffer, size_t length, bool present, double value,
                        const char *suffix)
{
    if (!present) snprintf(buffer, length, "UNKNOWN");
    else snprintf(buffer, length, "%.0f%s", value, suffix ? suffix : "");
}

static size_t dashboard_row_count(cJSON *usage)
{
    size_t count = 0;
    cJSON *snapshot;
    cJSON_ArrayForEach(snapshot, usage) {
        cJSON *windows = cJSON_GetObjectItemCaseSensitive(snapshot, "windows");
        size_t windows_count = cJSON_IsArray(windows) ? (size_t)cJSON_GetArraySize(windows) : 0;
        count += windows_count ? windows_count : 1;
    }
    return count;
}

static void draw_usage_row(int row, cJSON *snapshot, cJSON *window, const char *sent_at,
                           uint64_t frame_age_ms)
{
    char text[192], used[24], remaining[24], reset[28];
    const char *provider = json_string(snapshot, "provider_id");
    const char *source = json_string(snapshot, "source_kind");
    const char *label = window ? json_string(window, "label") : NULL;
    const char *unit = window ? json_string(window, "unit") : json_string(snapshot, "unit");
    const char *resets_at = window ? json_string(window, "resets_at") : NULL;
    const char *observed_at = json_string(snapshot, "observed_at");
    if (window) {
        double value;
        bool used_ok = json_number(window, "percent_used", &value);
        number_text(used, sizeof(used), used_ok, value, "%");
        bool remaining_ok = json_number(window, "percent_remaining", &value);
        number_text(remaining, sizeof(remaining), remaining_ok, value, "%");
        if ((!used_ok || !remaining_ok) && json_number(window, "used_units", &value)) {
            double limit;
            bool has_limit = json_number(window, "limit_units", &limit);
            snprintf(used, sizeof(used), "%.0f/%s", value, has_limit ? "LIMIT" : "?");
            if (has_limit) snprintf(used, sizeof(used), "%.0f/%.0f", value, limit);
            bool has_remaining = json_number(window, "remaining_units", &value);
            if (has_remaining) snprintf(remaining, sizeof(remaining), "%.0f %s", value, unit ? unit : "UNITS");
        }
        const char *reset_string = resets_at ? resets_at : "UNKNOWN";
        snprintf(reset, sizeof(reset), "%.24s", reset_string);
    } else {
        snprintf(used, sizeof(used), "NO WINDOWS");
        snprintf(remaining, sizeof(remaining), "STATUS %.14s", json_string(snapshot, "status") ? json_string(snapshot, "status") : "UNKNOWN");
        snprintf(reset, sizeof(reset), "UNKNOWN");
    }
    bool source_stale = false;
    const char *observed = json_string(snapshot, "observed_at");
    if (sent_at && observed) source_stale = meter_source_is_stale(sent_at, observed, frame_age_ms);
    snprintf(text, sizeof(text), "%.12s/%.8s %.12s U%s L%s %s O%.20s R%.20s%s",
             provider ? provider : "UNKNOWN", source ? source : "UNKNOWN",
             label ? label : "STATUS", used, remaining, unit ? unit : "UNKNOWN",
             observed_at ? observed_at : "UNKNOWN", reset,
             source_stale ? " SOURCE-STALE" : "");
    int y = 55 + row * 18;
    fill_rect(18, y - 2, LCD_WIDTH - 36, 17, (row & 1) ? 0x10A4 : 0x18E6);
    draw_text(24, y, text, source_stale ? 0xFD20 : 0xFFFF, 1, 126);
}

static void render_dashboard(cJSON *payload, uint32_t sequence, bool receive_stale,
                             const char *sent_at, uint64_t frame_age_ms, uint64_t scroll_offset)
{
    cJSON *usage = cJSON_GetObjectItemCaseSensitive(payload, "usage");
    size_t total = cJSON_IsArray(usage) ? dashboard_row_count(usage) : 0;
    const size_t visible = 13;
    size_t offset = total ? (size_t)(scroll_offset % total) : 0;
    clear_canvas(0x0861);
    draw_text(22, 16, "CODEX DESK METER  /  PROVIDER WINDOWS", 0x7FEF, 3, 65);
    char heading[96];
    snprintf(heading, sizeof(heading), "FRAME %" PRIu32 "   RX %s   SOURCE TIMES PRESERVED",
             sequence, receive_stale ? "STALE" : "OK");
    draw_text(24, 39, heading, receive_stale ? 0xFD20 : 0xC618, 2, 65);
    size_t index = 0, shown = 0;
    cJSON *snapshot;
    cJSON_ArrayForEach(snapshot, usage) {
        cJSON *windows = cJSON_GetObjectItemCaseSensitive(snapshot, "windows");
        int count = cJSON_IsArray(windows) ? cJSON_GetArraySize(windows) : 0;
        if (!count) {
            if (index >= offset && shown < visible) draw_usage_row((int)shown++, snapshot, NULL, sent_at, frame_age_ms);
            index++;
        } else {
            cJSON *window;
            cJSON_ArrayForEach(window, windows) {
                if (index >= offset && shown < visible) draw_usage_row((int)shown++, snapshot, window, sent_at, frame_age_ms);
                index++;
            }
        }
    }
    char footer[96];
    snprintf(footer, sizeof(footer), "WINDOWS %u-%u / %u    BOOT: NEXT SCREEN",
             total ? (unsigned)(offset + 1) : 0, (unsigned)(offset + shown), (unsigned)total);
    draw_text(24, 300, footer, 0x7FEF, 2, 65);
}

static void render_global(cJSON *payload, const char *sent_at, uint64_t frame_age_ms)
{
    cJSON *resets = cJSON_GetObjectItemCaseSensitive(payload, "global_resets");
    cJSON *selected = NULL;
    cJSON *reset;
    cJSON_ArrayForEach(reset, resets) {
        const char *source = json_string(reset, "source");
        if (source && strcmp(source, "codex-resets.com") == 0) { selected = reset; break; }
    }
    clear_canvas(0x0861);
    draw_text(22, 22, "GLOBAL RESET HISTORY", 0x7FEF, 3, 65);
    draw_text(28, 82, "SOURCE  CODEX-RESETS.COM", 0xFFFF, 3, 65);
    if (!selected) {
        draw_text(28, 142, "DEFAULT  /  NO RESET HISTORY", 0xFFE0, 3, 65);
        draw_text(28, 188, "NO OTHER PROVIDER RESET IS SUBSTITUTED", 0xC618, 2, 65);
        return;
    }
    const char *captured = json_string(selected, "captured_at");
    const char *latest = json_string(selected, "latest_reset_at");
    bool stale = cJSON_IsTrue(cJSON_GetObjectItemCaseSensitive(selected, "stale"));
    if (sent_at && captured && meter_source_is_stale(sent_at, captured, frame_age_ms)) stale = true;
    char line[128];
    snprintf(line, sizeof(line), "LOOKUP  %.32s%s", captured ? captured : "UNKNOWN", stale ? "   STALE" : "");
    draw_text(28, 118, line, stale ? 0xFD20 : 0xC618, 2, 65);
    if (!latest) {
        draw_text(28, 165, "LAST RESET  NONE", 0xFFE0, 3, 65);
        draw_text(28, 210, "DEFAULT DISPLAY: RESET HISTORY NOT PROVIDED", 0xC618, 2, 65);
        return;
    }
    snprintf(line, sizeof(line), "LATEST RESET  %.36s", latest);
    draw_text(28, 164, line, 0xFFFF, 2, 65);
    int64_t elapsed = 0;
    if (sent_at && meter_timestamp_delta_seconds(sent_at, latest, &elapsed) && elapsed >= 0) {
        if (frame_age_ms / 1000u < INT64_MAX - elapsed) elapsed += (int64_t)(frame_age_ms / 1000u);
        snprintf(line, sizeof(line), "ELAPSED  %" PRId64 " DAYS  %02" PRId64 " HOURS",
                 elapsed / 86400, (elapsed % 86400) / 3600);
        draw_text(28, 205, line, 0xFFE0, 3, 65);
    } else {
        draw_text(28, 205, "ELAPSED  UNKNOWN / FUTURE SOURCE VALUE", 0xFFE0, 2, 65);
    }
    draw_text(28, 270, "FORECAST IS NOT A SCHEDULE", 0xC618, 2, 65);
}

static void render_status(cJSON *payload, uint32_t sequence, bool has_frame,
                          bool receive_stale, const char *last_error,
                          const char *sent_at, uint64_t frame_age_ms)
{
    clear_canvas(0x0861);
    draw_text(22, 20, "DEVICE STATUS / RECOVERY", 0x7FEF, 3, 65);
    char line[128];
    if (!has_frame) snprintf(line, sizeof(line), "RECEIVER  WAITING FOR FIRST FRAME");
    else snprintf(line, sizeof(line), "SEQUENCE %" PRIu32 "  RECEIVE AGE %" PRIu64 " SEC%s",
                  sequence, frame_age_ms / 1000u, receive_stale ? "  STALE" : "");
    draw_text(28, 66, line, receive_stale ? 0xFD20 : 0xFFFF, 2, 65);
    snprintf(line, sizeof(line), "TRANSPORT ERROR  %.28s", last_error && *last_error ? last_error : "NONE");
    draw_text(28, 91, line, last_error && *last_error ? 0xFD20 : 0xC618, 2, 65);
    cJSON *usage = cJSON_GetObjectItemCaseSensitive(payload, "usage");
    int row = 0;
    cJSON *snapshot;
    cJSON_ArrayForEach(snapshot, usage) {
        if (row >= 7) break;
        const char *provider = json_string(snapshot, "provider_id");
        const char *status = json_string(snapshot, "status");
        const char *error = json_string(snapshot, "error_code");
        const char *observed = json_string(snapshot, "observed_at");
        bool source_stale = observed && sent_at && meter_source_is_stale(sent_at, observed, frame_age_ms);
        const char *last_good = json_string(snapshot, "last_good_at");
        const char *source = json_string(snapshot, "source_kind");
        snprintf(line, sizeof(line), "%.12s/%.8s %.8s OBS %.20s LAST GOOD %.20s ERR %.10s",
                 provider ? provider : "UNKNOWN", source ? source : "UNKNOWN",
                 status ? status : "UNKNOWN",
                 observed ? observed : "UNKNOWN", last_good ? last_good : "UNKNOWN",
                 error ? error : "NONE");
        draw_text(28, 130 + row * 22, line,
                  (source_stale || error) ? 0xFD20 : 0xFFFF, 1, 126);
        row++;
    }
    if (!has_frame) draw_text(28, 180, "LAST-GOOD CACHE IS EMPTY; LCD REMAINS ACTIVE", 0xC618, 2, 65);
    draw_text(28, 294, "BOOT: CYCLE DASHBOARD / GLOBAL / STATUS", 0x7FEF, 2, 65);
}

esp_err_t board_backlight_set(uint8_t brightness)
{
    if (!ledc_ready) return ESP_ERR_INVALID_STATE;
    uint32_t duty = 255u - brightness; /* board backlight is active-low */
    ESP_RETURN_ON_ERROR(ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_1, duty), TAG, "backlight duty");
    return ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_1);
}

int board_boot_level(void)
{
    return gpio_get_level(PIN_LCD_CS);
}

esp_err_t board_lcd_init(void)
{
    spi_line_config_t line_config = {
        .cs_io_type = IO_TYPE_GPIO, .cs_gpio_num = PIN_LCD_CS,
        .scl_io_type = IO_TYPE_GPIO, .scl_gpio_num = PIN_LCD_SCK,
        .sda_io_type = IO_TYPE_GPIO, .sda_gpio_num = PIN_LCD_SDO,
        .io_expander = NULL,
    };
    esp_lcd_panel_io_3wire_spi_config_t io_config = ST7701_PANEL_IO_3WIRE_SPI_CONFIG(line_config, 0);
    esp_lcd_panel_io_handle_t io = NULL;
    ESP_RETURN_ON_ERROR(esp_lcd_new_panel_io_3wire_spi(&io_config, &io), TAG, "panel IO init");

    esp_lcd_rgb_panel_config_t rgb = {0};
    rgb.clk_src = LCD_CLK_SRC_DEFAULT;
    rgb.psram_trans_align = 64;
    rgb.bounce_buffer_size_px = 10 * LCD_WIDTH;
    rgb.num_fbs = 2;
    rgb.data_width = 16;
    rgb.bits_per_pixel = 16;
    rgb.de_gpio_num = 40; rgb.pclk_gpio_num = 41;
    rgb.vsync_gpio_num = 39; rgb.hsync_gpio_num = 38;
    rgb.disp_gpio_num = -1;
    rgb.data_gpio_nums[0] = 21; rgb.data_gpio_nums[1] = 5; rgb.data_gpio_nums[2] = 45;
    rgb.data_gpio_nums[3] = 48; rgb.data_gpio_nums[4] = 47;
    rgb.data_gpio_nums[5] = 14; rgb.data_gpio_nums[6] = 13; rgb.data_gpio_nums[7] = 12;
    rgb.data_gpio_nums[8] = 11; rgb.data_gpio_nums[9] = 10; rgb.data_gpio_nums[10] = 9;
    rgb.data_gpio_nums[11] = 17; rgb.data_gpio_nums[12] = 46; rgb.data_gpio_nums[13] = 3;
    rgb.data_gpio_nums[14] = 8; rgb.data_gpio_nums[15] = 18;
    rgb.timings.pclk_hz = 18 * 1000 * 1000;
    rgb.timings.h_res = LCD_WIDTH; rgb.timings.v_res = LCD_HEIGHT;
    rgb.timings.hsync_back_porch = 30; rgb.timings.hsync_front_porch = 30; rgb.timings.hsync_pulse_width = 6;
    rgb.timings.vsync_back_porch = 20; rgb.timings.vsync_front_porch = 20; rgb.timings.vsync_pulse_width = 40;
    rgb.flags.fb_in_psram = true;

    st7701_vendor_config_t vendor = {0};
    vendor.rgb_config = &rgb;
    vendor.init_cmds = panel_commands;
    vendor.init_cmds_size = sizeof(panel_commands) / sizeof(panel_commands[0]);
    /* The LCD SPI pins are separate from the RGB bus on this board. Keep the
       panel IO alive through RGB startup, as in the manufacturer's factory BSP. */
    vendor.flags.enable_io_multiplex = 0;
    vendor.flags.mirror_by_cmd = 1;
    esp_lcd_panel_dev_config_t config = {
        .reset_gpio_num = PIN_LCD_RESET,
        .rgb_ele_order = LCD_RGB_ELEMENT_ORDER_RGB,
        .bits_per_pixel = 16,
        .vendor_config = &vendor,
    };
    ESP_RETURN_ON_ERROR(esp_lcd_new_panel_st7701(io, &config, &panel), TAG, "ST7701 panel create");
    ESP_RETURN_ON_ERROR(esp_lcd_panel_reset(panel), TAG, "panel reset");
    ESP_RETURN_ON_ERROR(esp_lcd_panel_init(panel), TAG, "panel init");

    gpio_config_t boot = {
        .pin_bit_mask = 1ULL << PIN_LCD_CS, .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_ENABLE, .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    ESP_RETURN_ON_ERROR(gpio_config(&boot), TAG, "BOOT input init after panel SPI");

    ledc_timer_config_t timer = {
        .speed_mode = LEDC_LOW_SPEED_MODE, .duty_resolution = LEDC_TIMER_8_BIT,
        .timer_num = LEDC_TIMER_3, .freq_hz = 50000, .clk_cfg = LEDC_SLOW_CLK_RC_FAST,
    };
    ESP_RETURN_ON_ERROR(ledc_timer_config(&timer), TAG, "backlight PWM timer");
    ledc_channel_config_t channel = {
        .gpio_num = PIN_BACKLIGHT, .speed_mode = LEDC_LOW_SPEED_MODE,
        .channel = LEDC_CHANNEL_1, .intr_type = LEDC_INTR_DISABLE,
        .timer_sel = LEDC_TIMER_3, .duty = 75, .hpoint = 0,
    };
    ESP_RETURN_ON_ERROR(ledc_channel_config(&channel), TAG, "backlight PWM channel");
    ledc_ready = true;
    ESP_RETURN_ON_ERROR(board_backlight_set(180), TAG, "initial backlight duty");

    canvas = (uint16_t *)heap_caps_malloc(FRAME_BYTES, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
    if (!canvas) return ESP_ERR_NO_MEM;
    clear_canvas(0x0861);
    ESP_LOGI(TAG, "LCD %dx%d RGB565; one 524800-byte canvas in PSRAM; RGB panel framebuffers=%u",
             LCD_WIDTH, LCD_HEIGHT, (unsigned)rgb.num_fbs);
    ESP_LOGI(TAG, "free PSRAM=%u bytes, internal=%u bytes",
             (unsigned)heap_caps_get_free_size(MALLOC_CAP_SPIRAM),
             (unsigned)heap_caps_get_free_size(MALLOC_CAP_INTERNAL));
    return ESP_OK;
}

esp_err_t board_lcd_present(const char *frame,
                            uint32_t sequence,
                            bool has_frame,
                            bool receive_stale,
                            const char *last_error,
                            meter_page_t page,
                            uint64_t monotonic_ms,
                            uint64_t frame_accepted_ms,
                            uint64_t scroll_offset,
                            bool show_fixture_splash)
{
    if (!panel || !canvas) return ESP_ERR_INVALID_STATE;
    cJSON *parsed = frame ? cJSON_Parse(frame) : NULL;
    cJSON *payload = parsed ? cJSON_GetObjectItemCaseSensitive(parsed, "payload") : NULL;
    uint64_t frame_age_ms = has_frame && monotonic_ms >= frame_accepted_ms ? monotonic_ms - frame_accepted_ms : 0;
    const char *sent_at = parsed ? json_string(parsed, "sent_at") : NULL;
    if (show_fixture_splash || !has_frame) {
        clear_canvas(0x0861);
        draw_text(24, 28, "CODEX DESK METER", 0x7FEF, 4, 65);
        draw_text(28, 110, "WAITING FOR PC FIXTURE FRAME", 0xFFFF, 3, 65);
        draw_text(28, 165, "USB SERIAL  /  115200 8N1", 0xC618, 2, 65);
        draw_text(28, 205, "BOOT CYCLES DASHBOARD, GLOBAL RESET, STATUS", 0xFFE0, 2, 65);
        draw_text(28, 276, "NO VALUES ARE INVENTED WHILE CACHE IS EMPTY", 0xC618, 2, 65);
    } else if (payload && page == METER_PAGE_DASHBOARD) {
        render_dashboard(payload, sequence, receive_stale, sent_at, frame_age_ms, scroll_offset);
    } else if (payload && page == METER_PAGE_GLOBAL_RESET) {
        render_global(payload, sent_at, frame_age_ms);
    } else {
        render_status(payload, sequence, has_frame, receive_stale, last_error, sent_at, frame_age_ms);
    }
    esp_err_t error = esp_lcd_panel_draw_bitmap(panel, 0, 0, LCD_WIDTH, LCD_HEIGHT, canvas);
    if (parsed) cJSON_Delete(parsed);
    return error;
}
