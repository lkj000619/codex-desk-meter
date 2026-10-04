#include "meter_gui.h"
#include "meter_state.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

int main(void)
{
    meter_gui_t gui;
    assert(meter_gui_init(&gui, NULL));
    assert(gui.canvas != NULL);

    meter_state_t state;
    meter_state_init(&state);

    /* Test 1: Empty dashboard render */
    meter_gui_render(&gui, &state, 1788998400LL, 5000);
    /* Verify canvas is not all zero / blank */
    size_t non_zero = 0;
    size_t total_px = LCD_LANDSCAPE_WIDTH * LCD_LANDSCAPE_HEIGHT;
    for (size_t i = 0; i < total_px; ++i) {
        if (gui.canvas[i] != COLOR_BG) non_zero++;
    }
    assert(non_zero > 100);

    /* Test 2: Populated dashboard render */
    state.usage_count = 2;
    strcpy(state.usage[0].provider_id, "openai");
    strcpy(state.usage[0].agent_id, "codex-cli");
    strcpy(state.usage[0].host_id, "terminal");
    state.usage[0].status = SNAPSHOT_STATUS_AVAILABLE;
    state.usage[0].window_count = 1;
    strcpy(state.usage[0].windows[0].window_id, "five-hour");
    state.usage[0].windows[0].percent_used = 42.5;
    state.usage[0].windows[0].has_percent = true;

    strcpy(state.usage[1].provider_id, "anthropic");
    strcpy(state.usage[1].agent_id, "claude-code");
    strcpy(state.usage[1].host_id, "terminal");
    state.usage[1].status = SNAPSHOT_STATUS_AVAILABLE;
    state.usage[1].window_count = 2;
    strcpy(state.usage[1].windows[0].window_id, "five-hour");
    state.usage[1].windows[0].percent_used = 68.0;
    state.usage[1].windows[0].has_percent = true;
    strcpy(state.usage[1].windows[1].window_id, "weekly");
    state.usage[1].windows[1].percent_used = 15.0;
    state.usage[1].windows[1].has_percent = true;

    state.screen_mode = SCREEN_DASHBOARD;
    meter_gui_render(&gui, &state, 1788998400LL, 10000);

    /* Test 3: Screen 1 Global resets render */
    state.screen_mode = SCREEN_GLOBAL_RESETS;
    state.global_reset_count = 1;
    strcpy(state.global_resets[0].source, "codex-resets.com");
    strcpy(state.global_resets[0].latest_reset_at, "2026-09-09T18:00:00Z");
    strcpy(state.global_resets[0].captured_at, "2026-09-10T00:00:00Z");
    state.global_resets[0].forecast_24h_percent = 78.5;
    state.global_resets[0].has_forecast_24h = true;

    meter_gui_render(&gui, &state, 1788998400LL, 15000);

    /* Test 4: Screen 2 Status and error render */
    state.screen_mode = SCREEN_STATUS_ERROR;
    meter_state_record_error(&state, "http_500", "upstream timeout");
    meter_gui_render(&gui, &state, 1788998400LL, 20000);

    /* Test 5: Native panel flush (320x820) */
    uint16_t *native_fb = (uint16_t *)malloc(LCD_PORTRAIT_WIDTH * LCD_PORTRAIT_HEIGHT * sizeof(uint16_t));
    assert(native_fb != NULL);

    /* Normal landscape rotation */
    meter_gui_flush_to_native(&gui, native_fb, ORIENTATION_LANDSCAPE_NORMAL);
    /* Inverted landscape rotation */
    meter_gui_flush_to_native(&gui, native_fb, ORIENTATION_LANDSCAPE_INVERTED);

    free(native_fb);
    meter_gui_deinit(&gui);

    printf("ALL GUI REGRESSION TESTS PASSED!\n");
    return 0;
}
