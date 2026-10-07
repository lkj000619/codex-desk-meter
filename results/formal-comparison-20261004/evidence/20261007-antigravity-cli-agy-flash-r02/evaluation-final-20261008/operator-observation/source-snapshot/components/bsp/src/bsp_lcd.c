#include "bsp_lcd.h"
#include "esp_lcd_panel_ops.h"
#include "esp_lcd_panel_rgb.h"
#include "driver/ledc.h"
#include "esp_log.h"
#include "esp_rom_sys.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <string.h>

static const char *TAG = "bsp_lcd";

static esp_lcd_panel_handle_t s_rgb_panel = NULL;
static uint16_t *s_fb0 = NULL;

typedef struct {
    uint8_t cmd;
    const uint8_t *data;
    uint8_t data_bytes;
    uint16_t delay_ms;
} st7701_cmd_t;

static const st7701_cmd_t s_init_cmds[] = {
    {0xFF, (const uint8_t []){0x77, 0x01, 0x00, 0x00, 0x13}, 5, 0},
    {0xEF, (const uint8_t []){0x08}, 1, 0},
    {0xFF, (const uint8_t []){0x77, 0x01, 0x00, 0x00, 0x10}, 5, 0},
    {0xC0, (const uint8_t []){0xE5, 0x02}, 2, 0},
    {0xC1, (const uint8_t []){0x15, 0x0A}, 2, 0},
    {0xC2, (const uint8_t []){0x07, 0x02}, 2, 0},
    {0xCC, (const uint8_t []){0x10}, 1, 0},
    {0xB0, (const uint8_t []){0x00, 0x08, 0x51, 0x0D, 0xCE, 0x06, 0x00, 0x08, 0x08, 0x24, 0x05, 0xD0, 0x0F, 0x6F, 0x36, 0x1F}, 16, 0},
    {0xB1, (const uint8_t []){0x00, 0x10, 0x4F, 0x0C, 0x11, 0x05, 0x00, 0x07, 0x07, 0x18, 0x02, 0xD3, 0x11, 0x6E, 0x34, 0x1F}, 16, 0},
    {0xFF, (const uint8_t []){0x77, 0x01, 0x00, 0x00, 0x11}, 5, 0},
    {0xB0, (const uint8_t []){0x4D}, 1, 0},
    {0xB1, (const uint8_t []){0x37}, 1, 0},
    {0xB2, (const uint8_t []){0x87}, 1, 0},
    {0xB3, (const uint8_t []){0x80}, 1, 0},
    {0xB5, (const uint8_t []){0x4A}, 1, 0},
    {0xB7, (const uint8_t []){0x85}, 1, 0},
    {0xB8, (const uint8_t []){0x21}, 1, 0},
    {0xB9, (const uint8_t []){0x00, 0x13}, 2, 0},
    {0xC0, (const uint8_t []){0x09}, 1, 0},
    {0xC1, (const uint8_t []){0x78}, 1, 0},
    {0xC2, (const uint8_t []){0x78}, 1, 0},
    {0xD0, (const uint8_t []){0x88}, 1, 0},
    {0xE0, (const uint8_t []){0x80, 0x00, 0x02}, 3, 100},
    {0xE1, (const uint8_t []){0x0F, 0xA0, 0x00, 0x00, 0x10, 0xA0, 0x00, 0x00, 0x00, 0x60, 0x60}, 11, 0},
    {0xE2, (const uint8_t []){0x30, 0x30, 0x60, 0x60, 0x45, 0xA0, 0x00, 0x00, 0x46, 0xA0, 0x00, 0x00, 0x00}, 13, 0},
    {0xE3, (const uint8_t []){0x00, 0x00, 0x33, 0x33}, 4, 0},
    {0xE4, (const uint8_t []){0x44, 0x44}, 2, 0},
    {0xE5, (const uint8_t []){0x0F, 0x4A, 0xA0, 0xA0, 0x11, 0x4A, 0xA0, 0xA0, 0x13, 0x4A, 0xA0, 0xA0, 0x15, 0x4A, 0xA0, 0xA0}, 16, 0},
    {0xE6, (const uint8_t []){0x00, 0x00, 0x33, 0x33}, 4, 0},
    {0xE7, (const uint8_t []){0x44, 0x44}, 2, 0},
    {0xE8, (const uint8_t []){0x10, 0x4A, 0xA0, 0xA0, 0x12, 0x4A, 0xA0, 0xA0, 0x14, 0x4A, 0xA0, 0xA0, 0x16, 0x4A, 0xA0, 0xA0}, 16, 0},
    {0xEB, (const uint8_t []){0x02, 0x00, 0x4E, 0x4E, 0xEE, 0x44, 0x00}, 7, 0},
    {0xED, (const uint8_t []){0xFF, 0xFF, 0x04, 0x56, 0x72, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x27, 0x65, 0x40, 0xFF, 0xFF}, 16, 0},
    {0xEF, (const uint8_t []){0x08, 0x08, 0x08, 0x40, 0x3F, 0x64}, 6, 0},
    {0xFF, (const uint8_t []){0x77, 0x01, 0x00, 0x00, 0x13}, 5, 0},
    {0xE8, (const uint8_t []){0x00, 0x0E}, 2, 0},
    {0xFF, (const uint8_t []){0x77, 0x01, 0x00, 0x00, 0x00}, 5, 0},
    {0x11, (const uint8_t []){0x00}, 0, 120},
    {0xFF, (const uint8_t []){0x77, 0x01, 0x00, 0x00, 0x13}, 5, 0},
    {0xE8, (const uint8_t []){0x00, 0x0C}, 2, 10},
    {0xE8, (const uint8_t []){0x00, 0x00}, 2, 0},
    {0xFF, (const uint8_t []){0x77, 0x01, 0x00, 0x00, 0x00}, 5, 0},
    {0x3A, (const uint8_t []){0x55}, 1, 0},
    {0x36, (const uint8_t []){0x00}, 1, 0},
    {0x35, (const uint8_t []){0x00}, 1, 0},
    {0x29, (const uint8_t []){0x00}, 0, 20},
};

static void spi_write_byte(bool is_data, uint8_t val)
{
    /* 9-bit transmission: bit 0 is DC (0=cmd, 1=data), bits 1..8 are MSB first byte */
    gpio_set_level(PIN_LCD_SPI_CS, 0);
    esp_rom_delay_us(1);

    /* Clock in D/C bit */
    gpio_set_level(PIN_LCD_SPI_SDO, is_data ? 1 : 0);
    gpio_set_level(PIN_LCD_SPI_SCK, 0);
    esp_rom_delay_us(1);
    gpio_set_level(PIN_LCD_SPI_SCK, 1);
    esp_rom_delay_us(1);

    /* Clock in 8 data bits */
    for (int i = 7; i >= 0; --i) {
        gpio_set_level(PIN_LCD_SPI_SDO, (val >> i) & 1);
        gpio_set_level(PIN_LCD_SPI_SCK, 0);
        esp_rom_delay_us(1);
        gpio_set_level(PIN_LCD_SPI_SCK, 1);
        esp_rom_delay_us(1);
    }

    gpio_set_level(PIN_LCD_SPI_CS, 1);
    esp_rom_delay_us(1);
}

static void send_st7701_cmd(uint8_t cmd, const uint8_t *data, uint8_t len)
{
    spi_write_byte(false, cmd);
    for (uint8_t i = 0; i < len; ++i) {
        spi_write_byte(true, data[i]);
    }
}

static void init_spi_pins(void)
{
    gpio_config_t conf = {
        .pin_bit_mask = (1ULL << PIN_LCD_SPI_CS) | (1ULL << PIN_LCD_SPI_SCK) | (1ULL << PIN_LCD_SPI_SDO) | (1ULL << PIN_LCD_RGB_RESET),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    gpio_config(&conf);

    gpio_set_level(PIN_LCD_SPI_CS, 1);
    gpio_set_level(PIN_LCD_SPI_SCK, 1);
    gpio_set_level(PIN_LCD_SPI_SDO, 1);

    /* Hardware reset ST7701 */
    gpio_set_level(PIN_LCD_RGB_RESET, 0);
    vTaskDelay(pdMS_TO_TICKS(20));
    gpio_set_level(PIN_LCD_RGB_RESET, 1);
    vTaskDelay(pdMS_TO_TICKS(120));
}

static void init_backlight_pwm(void)
{
    ledc_timer_config_t timer_conf = {
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .duty_resolution = LEDC_TIMER_8_BIT,
        .timer_num = LEDC_TIMER_3,
        .freq_hz = 50 * 1000,
        .clk_cfg = LEDC_AUTO_CLK,
    };
    ledc_timer_config(&timer_conf);

    ledc_channel_config_t ch_conf = {
        .gpio_num = PIN_LCD_BL,
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .channel = LEDC_CHANNEL_1,
        .intr_type = LEDC_INTR_DISABLE,
        .timer_sel = LEDC_TIMER_3,
        .duty = 0, /* Active-low: 0 is maximum brightness */
        .hpoint = 0,
    };
    ledc_channel_config(&ch_conf);
}

void bsp_lcd_set_backlight(uint8_t brightness)
{
    /* Active-low: 255 - brightness */
    uint32_t duty = 255 - brightness;
    ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_1, duty);
    ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_1);
}

esp_err_t bsp_lcd_init(void)
{
    ESP_LOGI(TAG, "Initializing ST7701 3-wire SPI and panel");
    init_spi_pins();

    /* Send initialization command sequence */
    size_t cmd_count = sizeof(s_init_cmds) / sizeof(s_init_cmds[0]);
    for (size_t i = 0; i < cmd_count; ++i) {
        send_st7701_cmd(s_init_cmds[i].cmd, s_init_cmds[i].data, s_init_cmds[i].data_bytes);
        if (s_init_cmds[i].delay_ms > 0) {
            vTaskDelay(pdMS_TO_TICKS(s_init_cmds[i].delay_ms));
        }
    }

    ESP_LOGI(TAG, "ST7701 init commands sent; initializing RGB panel");

    esp_lcd_rgb_panel_config_t rgb_config = {
        .clk_src = LCD_CLK_SRC_DEFAULT,
        .psram_trans_align = 64,
        .bounce_buffer_size_px = 10 * 320,
        .num_fbs = 1,
        .data_width = 16,
        .bits_per_pixel = 16,
        .de_gpio_num = PIN_LCD_RGB_DE,
        .pclk_gpio_num = PIN_LCD_RGB_PCLK,
        .vsync_gpio_num = PIN_LCD_RGB_VSYNC,
        .hsync_gpio_num = PIN_LCD_RGB_HSYNC,
        .flags.fb_in_psram = true,
        .disp_gpio_num = -1,
        .data_gpio_nums = {
            21, 5, 45, 48, 47,       /* B0..B4 */
            14, 13, 12, 11, 10, 9,   /* G0..G5 */
            17, 46, 3, 8, 18         /* R0..R4 */
        },
        .timings = {
            .pclk_hz = 18 * 1000 * 1000,
            .h_res = 320,
            .v_res = 820,
            .hsync_back_porch = 30,
            .hsync_front_porch = 30,
            .hsync_pulse_width = 6,
            .vsync_back_porch = 20,
            .vsync_front_porch = 20,
            .vsync_pulse_width = 40,
        },
    };

    esp_err_t ret = esp_lcd_new_rgb_panel(&rgb_config, &s_rgb_panel);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to create RGB panel: %s", esp_err_to_name(ret));
        return ret;
    }

    ret = esp_lcd_panel_init(s_rgb_panel);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to init RGB panel: %s", esp_err_to_name(ret));
        return ret;
    }

    ret = esp_lcd_rgb_panel_get_frame_buffer(s_rgb_panel, 1, (void **)&s_fb0);
    if (ret != ESP_OK || !s_fb0) {
        ESP_LOGE(TAG, "Failed to get framebuffer pointer: %s", esp_err_to_name(ret));
        return ret;
    }

    /* Initialize Backlight */
    init_backlight_pwm();
    bsp_lcd_set_backlight(255); /* Turn on at 100% brightness */
    ESP_LOGI(TAG, "LCD and Backlight ready (320x820 native / 820x320 landscape)");
    return ESP_OK;
}

#define FLUSH_TILE_SIZE 32

void bsp_lcd_flush(const uint16_t *canvas_820x320, display_orientation_t orientation)
{
    if (!s_fb0 || !canvas_820x320) return;

    /* Flush 820x320 canvas to 320x820 native framebuffer using cache-blocked tiles */
    if (orientation == ORIENTATION_LANDSCAPE_NORMAL) {
        for (int ty = 0; ty < 320; ty += FLUSH_TILE_SIZE) {
            int max_ly = (ty + FLUSH_TILE_SIZE > 320) ? 320 : (ty + FLUSH_TILE_SIZE);
            for (int tx = 0; tx < 820; tx += FLUSH_TILE_SIZE) {
                int max_lx = (tx + FLUSH_TILE_SIZE > 820) ? 820 : (tx + FLUSH_TILE_SIZE);
                for (int ly = ty; ly < max_ly; ++ly) {
                    const uint16_t *src_row = &canvas_820x320[ly * 820];
                    int px = ly;
                    for (int lx = tx; lx < max_lx; ++lx) {
                        int py = 819 - lx;
                        s_fb0[py * 320 + px] = src_row[lx];
                    }
                }
            }
        }
    } else {
        /* Inverted landscape (180 deg) */
        for (int ty = 0; ty < 320; ty += FLUSH_TILE_SIZE) {
            int max_ly = (ty + FLUSH_TILE_SIZE > 320) ? 320 : (ty + FLUSH_TILE_SIZE);
            for (int tx = 0; tx < 820; tx += FLUSH_TILE_SIZE) {
                int max_lx = (tx + FLUSH_TILE_SIZE > 820) ? 820 : (tx + FLUSH_TILE_SIZE);
                for (int ly = ty; ly < max_ly; ++ly) {
                    const uint16_t *src_row = &canvas_820x320[ly * 820];
                    int px = 319 - ly;
                    for (int lx = tx; lx < max_lx; ++lx) {
                        int py = lx;
                        s_fb0[py * 320 + px] = src_row[lx];
                    }
                }
            }
        }
    }
}
