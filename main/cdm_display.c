#include "cdm_display.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "driver/gpio.h"
#include "driver/ledc.h"
#include "esp_err.h"
#include "esp_check.h"
#include "esp_heap_caps.h"
#include "esp_lcd_panel_io_additions.h"
#include "esp_lcd_panel_ops.h"
#include "esp_lcd_panel_rgb.h"
#include "esp_lcd_st7701.h"
#include "esp_log.h"

#define LOGICAL_W 820
#define LOGICAL_H 320
#define PANEL_W 320
#define PANEL_H 820
#define COLOR_BG 0x0841
#define COLOR_PANEL 0x10A3
#define COLOR_PANEL_ALT 0x18E5
#define COLOR_WHITE 0xFFFF
#define COLOR_MUTED 0x9CF3
#define COLOR_CYAN 0x5DDF
#define COLOR_GREEN 0x7E8C
#define COLOR_YELLOW 0xFEC0
#define COLOR_RED 0xF986

static const char *TAG = "cdm_lcd";
static esp_lcd_panel_handle_t panel;
static uint16_t *native_frame;

static const uint8_t g0[] = {0x77,0x01,0x00,0x00,0x13};
static const uint8_t g1[] = {0x08};
static const uint8_t g2[] = {0x77,0x01,0x00,0x00,0x10};
static const uint8_t c0[] = {0xE5,0x02};
static const uint8_t c1[] = {0x15,0x0A};
static const uint8_t c2[] = {0x07,0x02};
static const uint8_t cc[] = {0x10};
static const uint8_t b0[] = {0x00,0x08,0x51,0x0D,0xCE,0x06,0x00,0x08,0x08,0x24,0x05,0xD0,0x0F,0x6F,0x36,0x1F};
static const uint8_t b1[] = {0x00,0x10,0x4F,0x0C,0x11,0x05,0x00,0x07,0x07,0x18,0x02,0xD3,0x11,0x6E,0x34,0x1F};
static const uint8_t unlock11[] = {0x77,0x01,0x00,0x00,0x11};
static const uint8_t one4d[] = {0x4D};
static const uint8_t one37[] = {0x37};
static const uint8_t one87[] = {0x87};
static const uint8_t one80[] = {0x80};
static const uint8_t one4a[] = {0x4A};
static const uint8_t one85[] = {0x85};
static const uint8_t one21[] = {0x21};
static const uint8_t two0013[] = {0x00,0x13};
static const uint8_t one09[] = {0x09};
static const uint8_t one78[] = {0x78};
static const uint8_t one88[] = {0x88};
static const uint8_t e0[] = {0x80,0x00,0x02};
static const uint8_t e1[] = {0x0F,0xA0,0x00,0x00,0x10,0xA0,0x00,0x00,0x00,0x60,0x60};
static const uint8_t e2[] = {0x30,0x30,0x60,0x60,0x45,0xA0,0x00,0x00,0x46,0xA0,0x00,0x00,0x00};
static const uint8_t e3[] = {0x00,0x00,0x33,0x33};
static const uint8_t e4[] = {0x44,0x44};
static const uint8_t e5[] = {0x0F,0x4A,0xA0,0xA0,0x11,0x4A,0xA0,0xA0,0x13,0x4A,0xA0,0xA0,0x15,0x4A,0xA0,0xA0};
static const uint8_t e8[] = {0x10,0x4A,0xA0,0xA0,0x12,0x4A,0xA0,0xA0,0x14,0x4A,0xA0,0xA0,0x16,0x4A,0xA0,0xA0};
static const uint8_t eb[] = {0x02,0x00,0x4E,0x4E,0xEE,0x44,0x00};
static const uint8_t ed[] = {0xFF,0xFF,0x04,0x56,0x72,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0x27,0x65,0x40,0xFF,0xFF};
static const uint8_t ef[] = {0x08,0x08,0x08,0x40,0x3F,0x64};
static const uint8_t bank13[] = {0x77,0x01,0x00,0x00,0x13};
static const uint8_t bank00[] = {0x77,0x01,0x00,0x00,0x00};
static const uint8_t e80e[] = {0x00,0x0E};
static const uint8_t e80c[] = {0x00,0x0C};
static const uint8_t e800[] = {0x00,0x00};
static const uint8_t format565[] = {0x55};
static const uint8_t orientation[] = {0x00};
static const uint8_t empty[] = {0x00};
static const st7701_lcd_init_cmd_t init_commands[] = {
    {0xFF,(uint8_t *)g0,5,0},{0xEF,(uint8_t *)g1,1,0},{0xFF,(uint8_t *)g2,5,0},
    {0xC0,(uint8_t *)c0,2,0},{0xC1,(uint8_t *)c1,2,0},{0xC2,(uint8_t *)c2,2,0},{0xCC,(uint8_t *)cc,1,0},
    {0xB0,(uint8_t *)b0,16,0},{0xB1,(uint8_t *)b1,16,0},{0xFF,(uint8_t *)unlock11,5,0},
    {0xB0,(uint8_t *)one4d,1,0},{0xB1,(uint8_t *)one37,1,0},{0xB2,(uint8_t *)one87,1,0},
    {0xB3,(uint8_t *)one80,1,0},{0xB5,(uint8_t *)one4a,1,0},{0xB7,(uint8_t *)one85,1,0},
    {0xB8,(uint8_t *)one21,1,0},{0xB9,(uint8_t *)two0013,2,0},{0xC0,(uint8_t *)one09,1,0},
    {0xC1,(uint8_t *)one78,1,0},{0xC2,(uint8_t *)one78,1,0},{0xD0,(uint8_t *)one88,1,0},
    {0xE0,(uint8_t *)e0,3,100},{0xE1,(uint8_t *)e1,11,0},{0xE2,(uint8_t *)e2,13,0},
    {0xE3,(uint8_t *)e3,4,0},{0xE4,(uint8_t *)e4,2,0},{0xE5,(uint8_t *)e5,16,0},
    {0xE6,(uint8_t *)e3,4,0},{0xE7,(uint8_t *)e4,2,0},{0xE8,(uint8_t *)e8,16,0},
    {0xEB,(uint8_t *)eb,7,0},{0xED,(uint8_t *)ed,16,0},{0xEF,(uint8_t *)ef,6,0},
    {0xFF,(uint8_t *)bank13,5,0},{0xE8,(uint8_t *)e80e,2,0},{0xFF,(uint8_t *)bank00,5,0},
    {0x11,(uint8_t *)empty,0,120},{0xFF,(uint8_t *)bank13,5,0},{0xE8,(uint8_t *)e80c,2,10},
    {0xE8,(uint8_t *)e800,2,0},{0xFF,(uint8_t *)bank00,5,0},{0x3A,(uint8_t *)format565,1,0},
    {0x36,(uint8_t *)orientation,1,0},{0x35,(uint8_t *)empty,1,0},{0x29,(uint8_t *)empty,0,20},
};

static const uint8_t font_digits[10][5] = {
    {0x3E,0x51,0x49,0x45,0x3E},{0x00,0x42,0x7F,0x40,0x00},{0x42,0x61,0x51,0x49,0x46},
    {0x21,0x41,0x45,0x4B,0x31},{0x18,0x14,0x12,0x7F,0x10},{0x27,0x45,0x45,0x45,0x39},
    {0x3C,0x4A,0x49,0x49,0x30},{0x01,0x71,0x09,0x05,0x03},{0x36,0x49,0x49,0x49,0x36},
    {0x06,0x49,0x49,0x29,0x1E}
};

static void fill_rect(int x, int y, int w, int h, uint16_t color) {
    if (x < 0) { w += x; x = 0; }
    if (y < 0) { h += y; y = 0; }
    if (x + w > LOGICAL_W) w = LOGICAL_W - x;
    if (y + h > LOGICAL_H) h = LOGICAL_H - y;
    for (int row = 0; row < h; ++row) for (int col = 0; col < w; ++col) {
        int panel_x = PANEL_W - 1 - (y + row);
        int panel_y = x + col;
        native_frame[panel_y * PANEL_W + panel_x] = color;
    }
}

static const uint8_t *glyph(char c) {
    static const uint8_t letters[26][5] = {
        {0x7E,0x11,0x11,0x11,0x7E},{0x7F,0x49,0x49,0x49,0x36},{0x3E,0x41,0x41,0x41,0x22},
        {0x7F,0x41,0x41,0x22,0x1C},{0x7F,0x49,0x49,0x49,0x41},{0x7F,0x09,0x09,0x09,0x01},
        {0x3E,0x41,0x49,0x49,0x7A},{0x7F,0x08,0x08,0x08,0x7F},{0x00,0x41,0x7F,0x41,0x00},
        {0x20,0x40,0x41,0x3F,0x01},{0x7F,0x08,0x14,0x22,0x41},{0x7F,0x40,0x40,0x40,0x40},
        {0x7F,0x02,0x0C,0x02,0x7F},{0x7F,0x04,0x08,0x10,0x7F},{0x3E,0x41,0x41,0x41,0x3E},
        {0x7F,0x09,0x09,0x09,0x06},{0x3E,0x41,0x51,0x21,0x5E},{0x7F,0x09,0x19,0x29,0x46},
        {0x46,0x49,0x49,0x49,0x31},{0x01,0x01,0x7F,0x01,0x01},{0x3F,0x40,0x40,0x40,0x3F},
        {0x1F,0x20,0x40,0x20,0x1F},{0x3F,0x40,0x38,0x40,0x3F},{0x63,0x14,0x08,0x14,0x63},
        {0x07,0x08,0x70,0x08,0x07},{0x61,0x51,0x49,0x45,0x43}
    };
    if (c >= 'a' && c <= 'z') c = (char)(c - 'a' + 'A');
    if (c >= '0' && c <= '9') return font_digits[c - '0'];
    if (c >= 'A' && c <= 'Z') return letters[c - 'A'];
    static const uint8_t blank[5] = {0,0,0,0,0};
    static const uint8_t colon[5] = {0,0x36,0x36,0,0};
    static const uint8_t dash[5] = {0x08,0x08,0x08,0x08,0x08};
    static const uint8_t dot[5] = {0,0x60,0x60,0,0};
    static const uint8_t slash[5] = {0x20,0x10,0x08,0x04,0x02};
    static const uint8_t percent[5] = {0x63,0x13,0x08,0x64,0x63};
    if (c == ':') return colon;
    if (c == '-') return dash;
    if (c == '.') return dot;
    if (c == '/') return slash;
    if (c == '%') return percent;
    return blank;
}

static void draw_text(int x, int y, const char *text, int scale, uint16_t color) {
    for (const char *p = text; *p != '\0' && x < LOGICAL_W - 6 * scale; ++p, x += 6 * scale) {
        const uint8_t *shape = glyph(*p);
        for (int col = 0; col < 5; ++col) for (int row = 0; row < 7; ++row)
            if ((shape[col] >> row) & 1) fill_rect(x + col * scale, y + row * scale, scale, scale, color);
    }
}

static void draw_header(const char *title, CdmScreen screen, bool stale) {
    fill_rect(0, 0, LOGICAL_W, LOGICAL_H, COLOR_BG);
    fill_rect(0, 0, LOGICAL_W, 54, COLOR_PANEL);
    draw_text(24, 15, "CODEX METER", 3, COLOR_WHITE);
    draw_text(300, 18, title, 2, COLOR_CYAN);
    const char *page = screen == CDM_SCREEN_DASHBOARD ? "1 DASHBOARD" : screen == CDM_SCREEN_GLOBAL_RESET ? "2 GLOBAL RESET" : "3 STATUS";
    draw_text(650, 18, page, 2, COLOR_WHITE);
    fill_rect(0, 53, LOGICAL_W, 2, stale ? COLOR_RED : COLOR_CYAN);
}

static void draw_dashboard(const CdmReceiver *receiver, int64_t now_epoch) {
    size_t total = 0;
    for (size_t i = 0; i < receiver->usage_count; ++i) total += receiver->usage[i].window_count;
    draw_text(24, 72, "QUOTA WINDOWS - SOURCE OBSERVATION TIMES", 2, COLOR_MUTED);
    size_t start = cdm_dashboard_page(total, (uint64_t)(now_epoch > 0 ? now_epoch : 0)) * 8u;
    size_t end = start + 8u < total ? start + 8u : total;
    char page[48];
    snprintf(page, sizeof(page), "WINDOWS %u-%u OF %u", (unsigned)(total == 0 ? 0 : start + 1), (unsigned)end, (unsigned)total);
    draw_text(610, 72, page, 1, COLOR_CYAN);
    for (size_t card = 0; card < 8 && start + card < total; ++card) {
        size_t target = start + card;
        const CdmUsage *usage = NULL;
        const CdmWindow *window = NULL;
        for (size_t i = 0; i < receiver->usage_count && window == NULL; ++i) {
            if (target < receiver->usage[i].window_count) {
                usage = &receiver->usage[i];
                window = &usage->windows[target];
            } else target -= receiver->usage[i].window_count;
        }
        if (usage == NULL || window == NULL) continue;
        int col = (int)(card % 4u);
        int row = (int)(card / 4u);
        int x = 20 + col * 198;
        int y = 104 + row * 96;
        fill_rect(x, y, 186, 82, (card % 2u) ? COLOR_PANEL : COLOR_PANEL_ALT);
        char identity[48];
        snprintf(identity, sizeof(identity), "%.20s/%.25s", usage->provider_id,
                 usage->agent_id[0] ? usage->agent_id : "UNKNOWN");
        draw_text(x + 8, y + 4, identity, 1, COLOR_CYAN);
        draw_text(x + 8, y + 16, window->label, 1, COLOR_WHITE);
        char value[24];
        if (window->has_percent_remaining) snprintf(value, sizeof(value), "%.0f%% LEFT", window->percent_remaining);
        else if (window->has_percent_used) snprintf(value, sizeof(value), "%.0f%% USED", window->percent_used);
        else snprintf(value, sizeof(value), "NO VALUE");
        draw_text(x + 8, y + 27, value, 2, usage->stale ? COLOR_YELLOW : COLOR_GREEN);
        char reset[32], observed[32];
        const char *when = window->resets_at;
        if (strcmp(window->reset_status, "expired") == 0) snprintf(reset, sizeof(reset), "RST EXPIRED");
        else if (when[0] != '\0' && strlen(when) >= 16) snprintf(reset, sizeof(reset), "RST %.11s", when + 5);
        else snprintf(reset, sizeof(reset), "RST UNKNOWN");
        if (strlen(usage->observed_at) >= 16) snprintf(observed, sizeof(observed), "OBS %.11s", usage->observed_at + 5);
        else snprintf(observed, sizeof(observed), "OBS UNKNOWN");
        draw_text(x + 8, y + 51, reset, 1, window->reset_status[0] == 'e' ? COLOR_YELLOW : COLOR_MUTED);
        draw_text(x + 8, y + 65, observed, 1, usage->stale ? COLOR_YELLOW : COLOR_MUTED);
    }
    if (total == 0) draw_text(24, 132, "WAITING FOR A PC SNAPSHOT", 3, COLOR_YELLOW);
    draw_text(24, 300, "BOOT: CHANGE SCREEN   PC REFRESH: RUN THE COLLECTOR AGAIN", 1, COLOR_MUTED);
}

static void draw_global_reset(const CdmReceiver *receiver, int64_t now_epoch) {
    const CdmGlobalReset *selected = NULL;
    for (size_t i = 0; i < receiver->reset_count; ++i)
        if (strcmp(receiver->global_resets[i].source, "codex-resets.com") == 0) selected = &receiver->global_resets[i];
    if (selected == NULL || !selected->has_latest_reset) {
        draw_text(32, 104, "NO GLOBAL RESET HISTORY", 3, COLOR_YELLOW);
        draw_text(32, 154, "ELAPSED TIME IS UNKNOWN - DEFAULT VIEW", 2, COLOR_MUTED);
        return;
    }
    draw_text(32, 78, "LATEST OBSERVED RESET", 2, COLOR_MUTED);
    draw_text(32, 116, selected->latest_reset_at, 3, COLOR_WHITE);
    int64_t reset_epoch;
    if (cdm_parse_epoch(selected->latest_reset_at, &reset_epoch) && now_epoch >= reset_epoch) {
        int64_t age = now_epoch - reset_epoch;
        char elapsed[48];
        snprintf(elapsed, sizeof(elapsed), "%lld DAYS  %02lld HOURS AGO", (long long)(age / 86400), (long long)((age % 86400) / 3600));
        draw_text(32, 173, elapsed, 3, COLOR_CYAN);
    } else {
        draw_text(32, 173, "ELAPSED TIME UNKNOWN", 3, COLOR_YELLOW);
    }
    draw_text(32, 244, "SOURCE: CODEX-RESETS.COM", 2, COLOR_GREEN);
    char captured[56];
    snprintf(captured, sizeof(captured), "CAPTURED %s", selected->captured_at);
    draw_text(32, 275, captured, 1, selected->stale ? COLOR_YELLOW : COLOR_MUTED);
}

static void draw_status(const CdmReceiver *receiver, bool rtc_ready) {
    draw_text(28, 78, receiver->has_good_frame ? "HOST LINK: FRAME RECEIVED" : "HOST LINK: WAITING", 2,
              receiver->has_good_frame ? COLOR_GREEN : COLOR_YELLOW);
    char line[80];
    snprintf(line, sizeof(line), "SEQUENCE %lu   SNAPSHOTS %u   RESET SOURCES %u",
             (unsigned long)receiver->sequence, (unsigned)receiver->usage_count, (unsigned)receiver->reset_count);
    draw_text(28, 112, line, 2, COLOR_WHITE);
    snprintf(line, sizeof(line), "LAST GOOD %lld", (long long)receiver->last_good_epoch);
    draw_text(28, 148, line, 2, COLOR_MUTED);
    draw_text(28, 184, receiver->stale ? "DEVICE CACHE: STALE - LAST GOOD KEPT" : "DEVICE CACHE: CURRENT", 2,
              receiver->stale ? COLOR_YELLOW : COLOR_GREEN);
    draw_text(28, 220, rtc_ready ? "PCF85063 RTC: HOLDOVER READY" : "PCF85063 RTC: WAITING FOR HOST TIME", 2,
              rtc_ready ? COLOR_CYAN : COLOR_MUTED);
    snprintf(line, sizeof(line), "LAST RECEIVER RESULT %d", (int)receiver->last_error);
    draw_text(28, 264, line, 2, COLOR_MUTED);
    int y = 286;
    for (size_t i = 0; i < receiver->usage_count && i < 2; ++i) {
        const CdmUsage *usage = &receiver->usage[i];
        if (strcmp(usage->status, "available") == 0 && !usage->stale) continue;
        snprintf(line, sizeof(line), "%.20s %.12s %.40s", usage->provider_id, usage->status,
                 usage->error_code[0] ? usage->error_code : "STALE");
        draw_text(380, y, line, 1, COLOR_YELLOW);
        y += 12;
    }
}

bool cdm_display_init(void) {
    ledc_timer_config_t timer = {.speed_mode = LEDC_LOW_SPEED_MODE, .duty_resolution = LEDC_TIMER_8_BIT,
        .timer_num = LEDC_TIMER_3, .freq_hz = 50000, .clk_cfg = LEDC_SLOW_CLK_RC_FAST};
    ledc_channel_config_t channel = {.gpio_num = GPIO_NUM_6, .speed_mode = LEDC_LOW_SPEED_MODE,
        .channel = LEDC_CHANNEL_1, .intr_type = LEDC_INTR_DISABLE, .timer_sel = LEDC_TIMER_3,
        .duty = 255, .hpoint = 0};
    if (ledc_timer_config(&timer) != ESP_OK || ledc_channel_config(&channel) != ESP_OK) {
        ESP_LOGE(TAG, "backlight PWM init failed");
        return false;
    }

    spi_line_config_t line = {.cs_io_type = IO_TYPE_GPIO, .cs_gpio_num = GPIO_NUM_0,
        .scl_io_type = IO_TYPE_GPIO, .scl_gpio_num = GPIO_NUM_2,
        .sda_io_type = IO_TYPE_GPIO, .sda_gpio_num = GPIO_NUM_1, .io_expander = NULL};
    esp_lcd_panel_io_3wire_spi_config_t io_config = ST7701_PANEL_IO_3WIRE_SPI_CONFIG(line, 0);
    esp_lcd_panel_io_handle_t io = NULL;
    if (esp_lcd_new_panel_io_3wire_spi(&io_config, &io) != ESP_OK) {
        ESP_LOGE(TAG, "ST7701 command bus init failed");
        return false;
    }

    static const int rgb_pins[16] = {21,5,45,48,47,14,13,12,11,10,9,17,46,3,8,18};
    esp_lcd_rgb_panel_config_t rgb = {0};
    rgb.clk_src = LCD_CLK_SRC_DEFAULT;
    rgb.psram_trans_align = 64;
    rgb.bounce_buffer_size_px = 10 * PANEL_W;
    rgb.num_fbs = 2;
    rgb.data_width = 16;
    rgb.bits_per_pixel = 16;
    rgb.de_gpio_num = 40;
    rgb.pclk_gpio_num = 41;
    rgb.vsync_gpio_num = 39;
    rgb.hsync_gpio_num = 38;
    rgb.flags.fb_in_psram = true;
    for (int i = 0; i < 16; ++i) rgb.data_gpio_nums[i] = rgb_pins[i];
    rgb.timings.pclk_hz = 18000000;
    rgb.timings.h_res = PANEL_W;
    rgb.timings.v_res = PANEL_H;
    rgb.timings.hsync_back_porch = 30;
    rgb.timings.hsync_front_porch = 30;
    rgb.timings.hsync_pulse_width = 6;
    rgb.timings.vsync_back_porch = 20;
    rgb.timings.vsync_front_porch = 20;
    rgb.timings.vsync_pulse_width = 40;
    st7701_vendor_config_t vendor = {0};
    vendor.rgb_config = &rgb;
    vendor.init_cmds = init_commands;
    vendor.init_cmds_size = sizeof(init_commands) / sizeof(init_commands[0]);
    vendor.flags.mirror_by_cmd = 1;
    vendor.flags.enable_io_multiplex = 0;
    const esp_lcd_panel_dev_config_t config = {.reset_gpio_num = GPIO_NUM_16,
        .rgb_ele_order = LCD_RGB_ELEMENT_ORDER_RGB, .bits_per_pixel = 16, .vendor_config = &vendor};
    if (esp_lcd_new_panel_st7701(io, &config, &panel) != ESP_OK ||
        esp_lcd_panel_reset(panel) != ESP_OK || esp_lcd_panel_init(panel) != ESP_OK) {
        ESP_LOGE(TAG, "ST7701 panel initialization failed");
        return false;
    }

    native_frame = heap_caps_calloc(PANEL_W * PANEL_H, sizeof(uint16_t), MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
    if (native_frame == NULL) native_frame = calloc(PANEL_W * PANEL_H, sizeof(uint16_t));
    if (native_frame == NULL) return ESP_ERR_NO_MEM;
    ESP_LOGI(TAG, "ST7701 initialized, logical landscape 820x320");
    return true;
}

void cdm_display_render(const CdmReceiver *receiver, CdmScreen screen, int64_t now_epoch, bool rtc_ready) {
    if (panel == NULL || native_frame == NULL) return;
    bool stale = receiver->stale;
    for (size_t i = 0; i < receiver->usage_count; ++i) stale = stale || receiver->usage[i].stale;
    for (size_t i = 0; i < receiver->reset_count; ++i) stale = stale || receiver->global_resets[i].stale;
    const char *title = screen == CDM_SCREEN_DASHBOARD ? "USAGE" : screen == CDM_SCREEN_GLOBAL_RESET ? "GLOBAL RESET" : "DEVICE STATUS";
    draw_header(title, screen, stale);
    if (screen == CDM_SCREEN_DASHBOARD) draw_dashboard(receiver, now_epoch);
    else if (screen == CDM_SCREEN_GLOBAL_RESET) draw_global_reset(receiver, now_epoch);
    else draw_status(receiver, rtc_ready);
    esp_err_t result = esp_lcd_panel_draw_bitmap(panel, 0, 0, PANEL_W, PANEL_H, native_frame);
    if (result != ESP_OK) ESP_LOGE(TAG, "framebuffer transfer failed: %s", esp_err_to_name(result));
}
