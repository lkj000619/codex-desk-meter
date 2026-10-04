#include "meter_state.h"
#include "meter_parser.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

static void test_state_sequence(void)
{
    meter_state_t state;
    meter_state_init(&state);

    meter_frame_t f1;
    memset(&f1, 0, sizeof(f1));
    f1.sequence = 7;
    strcpy(f1.protocol, "cdm/1");
    strcpy(f1.sent_at, "2026-09-10T00:00:00Z");

    char err[32] = {0};
    int64_t t0 = 1788998400LL; /* 2026-09-10T00:00:00Z */

    /* First frame: seq 7 accepted */
    assert(meter_state_process_frame(&state, &f1, t0, err));
    assert(state.has_sequence);
    assert(state.current_sequence == 7);

    /* Duplicate frame: seq 7 rejected */
    assert(!meter_state_process_frame(&state, &f1, t0, err));
    assert(strcmp(err, "DUPLICATE_SEQUENCE") == 0);
    assert(state.current_sequence == 7);

    /* Out of order: seq 1 rejected */
    f1.sequence = 1;
    assert(!meter_state_process_frame(&state, &f1, t0, err));
    assert(strcmp(err, "OUT_OF_ORDER_SEQUENCE") == 0);
    assert(state.current_sequence == 7);

    /* Newer: seq 8 accepted */
    f1.sequence = 8;
    assert(meter_state_process_frame(&state, &f1, t0, err));
    assert(state.current_sequence == 8);

    /* Test wrap around: from 4294967295 to 0 */
    state.current_sequence = 4294967295u;
    f1.sequence = 0;
    assert(meter_state_process_frame(&state, &f1, t0, err));
    assert(state.current_sequence == 0);

    /* 0 followed by 1 */
    f1.sequence = 1;
    assert(meter_state_process_frame(&state, &f1, t0, err));
    assert(state.current_sequence == 1);

    printf("test_state_sequence passed\n");
}

static void test_stale_and_recovery(void)
{
    meter_state_t state;
    meter_state_init(&state);

    int64_t t0 = 1788998400LL; /* 2026-09-10T00:00:00Z */

    meter_frame_t frame;
    memset(&frame, 0, sizeof(frame));
    frame.sequence = 1;
    strcpy(frame.protocol, "cdm/1");
    strcpy(frame.sent_at, "2026-09-10T00:00:00Z");
    frame.usage_count = 1;
    strcpy(frame.usage[0].provider_id, "openai");
    strcpy(frame.usage[0].observed_at, "2026-09-10T00:00:00Z");
    frame.usage[0].status = SNAPSHOT_STATUS_AVAILABLE;

    char err[32] = {0};
    assert(meter_state_process_frame(&state, &frame, t0, err));
    assert(!state.is_stale);
    assert(state.usage_count == 1);

    /* Test boundary: t0 + 299s -> NOT stale */
    meter_state_update_stale(&state, t0 + 299);
    assert(!state.is_stale);
    assert(!state.usage[0].stale);

    /* Test boundary: t0 + 300s -> STALE */
    meter_state_update_stale(&state, t0 + 300);
    assert(state.is_stale);
    assert(state.usage[0].stale);

    /* Test error recording: preserves last-good usage */
    meter_state_record_error(&state, "http_500", "server error");
    assert(state.has_error);
    assert(strcmp(state.last_error_code, "http_500") == 0);
    assert(state.usage_count == 1);
    assert(strcmp(state.usage[0].provider_id, "openai") == 0);

    /* Test recovery with fresh frame at t0 + 400 */
    frame.sequence = 2;
    strcpy(frame.sent_at, "2026-09-10T00:06:40Z");
    strcpy(frame.usage[0].observed_at, "2026-09-10T00:06:40Z");
    assert(meter_state_process_frame(&state, &frame, t0 + 400, err));
    assert(!state.has_error);
    assert(state.last_error_code[0] == '\0');
    assert(!state.is_stale);
    assert(!state.usage[0].stale);

    printf("test_stale_and_recovery passed\n");
}

static void test_screen_cycle_and_debounce(void)
{
    meter_state_t state;
    meter_state_init(&state);
    assert(state.screen_mode == SCREEN_DASHBOARD);

    /* First press at 1000ms: switches to SCREEN_GLOBAL_RESETS */
    assert(meter_state_cycle_screen(&state, 1000));
    assert(state.screen_mode == SCREEN_GLOBAL_RESETS);

    /* Rapid press at 1150ms (<300ms): debounced / ignored */
    assert(!meter_state_cycle_screen(&state, 1150));
    assert(state.screen_mode == SCREEN_GLOBAL_RESETS);

    /* Press at 1350ms (>=300ms): switches to SCREEN_STATUS_ERROR */
    assert(meter_state_cycle_screen(&state, 1350));
    assert(state.screen_mode == SCREEN_STATUS_ERROR);

    /* Press at 1700ms: switches back to SCREEN_DASHBOARD */
    assert(meter_state_cycle_screen(&state, 1700));
    assert(state.screen_mode == SCREEN_DASHBOARD);

    printf("test_screen_cycle_and_debounce passed\n");
}

int main(void)
{
    test_state_sequence();
    test_stale_and_recovery();
    test_screen_cycle_and_debounce();
    printf("ALL METER_STATE TESTS PASSED!\n");
    return 0;
}
