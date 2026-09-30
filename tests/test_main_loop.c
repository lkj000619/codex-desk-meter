/* Executes the real firmware main loop and receiver with simulated hardware.
 * Catches UART-vs-native-USB routing and delayed BOOT rendering, not source text.
 * Display calls are observation points; physical LCD timing remains a board test. */
#include <assert.h>
#include <setjmp.h>
#include <stdio.h>
#include <string.h>
#include <sys/time.h>
#include "test_idf.h"
int simulated_settimeofday(const struct timeval *tv, const void *zone);
#define settimeofday simulated_settimeofday
#include "../main/main.c"
#undef settimeofday

static jmp_buf finished;
static uint32_t tick, first_button_draw = UINT32_MAX, first_packet_draw = UINT32_MAX;
static unsigned page_transitions;
static CdmScreen previous_screen = CDM_SCREEN_DASHBOARD;
static bool usb_ready, delivered, simulate_button;
static const char packet[] =
    "{\"integrity\":{\"algorithm\":\"crc32\",\"value\":\"BE8028D7\"},"
    "\"payload\":{\"global_resets\":[],\"usage\":[]},"
    "\"protocol\":\"cdm/1\",\"sent_at\":\"2026-09-10T00:00:00Z\",\"sequence\":1}\n";
int simulated_settimeofday(const struct timeval *tv, const void *zone) {
    (void)tv; (void)zone; return 0;
}
void esp_log_level_set(const char *name, int level) { (void)name; (void)level; }
void *heap_caps_malloc(size_t n, int flags) { (void)flags; return malloc(n); }
esp_err_t gpio_config(const gpio_config_t *config) { (void)config; return ESP_OK; }
int gpio_get_level(int pin) { (void)pin; return !(simulate_button && tick >= 100 && tick < 1400); }
uint32_t xTaskGetTickCount(void) { return tick; }
void vTaskDelay(uint32_t wait) { tick += wait; if (tick >= 1750) longjmp(finished, 1); }
int uart_read_bytes(int port, void *out, size_t n, uint32_t wait) {
    (void)port; (void)out; (void)n; (void)wait; return 0;
}
esp_err_t uart_driver_install(int p, int r, int t, int q, void *e, int f) {
    (void)p; (void)r; (void)t; (void)q; (void)e; (void)f; return ESP_OK;
}
esp_err_t uart_param_config(int p, const uart_config_t *c) { (void)p; (void)c; return ESP_OK; }
esp_err_t uart_set_pin(int p, int a, int b, int c, int d) {
    (void)p; (void)a; (void)b; (void)c; (void)d; return ESP_OK;
}
esp_err_t usb_serial_jtag_driver_install(const usb_serial_jtag_driver_config_t *c) {
    (void)c; usb_ready = true; return ESP_OK;
}
int usb_serial_jtag_read_bytes(void *out, size_t n, uint32_t wait) {
    (void)wait;
    if (!usb_ready || delivered || tick < 200) return 0;
    assert(n >= sizeof(packet) - 1);
    memcpy(out, packet, sizeof(packet) - 1);
    delivered = true;
    return (int)sizeof(packet) - 1;
}
int usb_serial_jtag_write_bytes(const void *data, size_t n, uint32_t wait) {
    (void)data; (void)wait; return (int)n;
}
bool cdm_rtc_init(int64_t *epoch) { (void)epoch; return false; }
bool cdm_rtc_sync(int64_t epoch) { (void)epoch; return false; }
bool cdm_rtc_read(int64_t *epoch) { (void)epoch; return false; }
bool cdm_display_init(void) { return true; }
void cdm_display_render(const CdmReceiver *state, CdmScreen page, int64_t now, bool rtc) {
    (void)now; (void)rtc;
    if (page != previous_screen) {
        ++page_transitions;
        previous_screen = page;
        if (first_button_draw == UINT32_MAX) first_button_draw = tick;
    }
    if (state->has_good_frame && first_packet_draw == UINT32_MAX) first_packet_draw = tick;
}
int main(int argc, char **argv) {
    assert(argc == 2);
    simulate_button = strcmp(argv[1], "boot") == 0;
    if (setjmp(finished) == 0) app_main();
    if (simulate_button) {
        /* Stable press occurs at 150 ms; maximum allowed delay is 300 ms. */
        assert(first_button_draw >= 150 && first_button_draw <= 450);
        assert(page_transitions == 1); /* Holding 1.3 seconds must not repeat. */
        printf("BOOT stable-to-render=%u ms, held press transitions=%u\n",
               first_button_draw - 150, page_transitions);
    } else {
        assert(receiver.has_good_frame && receiver.sequence == 1);
        assert(first_packet_draw >= 200 && first_packet_draw <= 2200);
        printf("Native USB packet-to-render=%u ms\n", first_packet_draw - 200);
    }
    free(line_buffer);
    return 0;
}
