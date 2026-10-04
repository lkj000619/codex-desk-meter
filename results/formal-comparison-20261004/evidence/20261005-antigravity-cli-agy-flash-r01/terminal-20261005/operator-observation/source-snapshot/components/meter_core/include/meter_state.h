#ifndef METER_STATE_H
#define METER_STATE_H

#include "meter_types.h"
#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    bool has_sequence;
    uint32_t current_sequence;
    int64_t last_receive_time; /* epoch seconds */
    char last_receive_stamp[METER_MAX_STRING_LEN];

    /* Last-good data */
    meter_snapshot_t usage[METER_MAX_SNAPSHOTS];
    size_t usage_count;
    meter_global_reset_t global_resets[METER_MAX_GLOBAL_RESETS];
    size_t global_reset_count;
    int64_t last_good_time; /* epoch seconds */
    char last_good_stamp[METER_MAX_STRING_LEN];

    /* Error and stale state */
    bool has_error;
    char last_error_code[32];
    char last_error_reason[METER_MAX_REASON_LEN];
    bool is_stale;

    /* Screen navigation */
    screen_mode_t screen_mode;
    uint32_t last_screen_switch_ms;

    /* Autonomous orientation (from IMU) */
    display_orientation_t orientation;
} meter_state_t;

/* Initialize state */
void meter_state_init(meter_state_t *state);

/* Process a parsed frame */
bool meter_state_process_frame(meter_state_t *state, const meter_frame_t *frame, int64_t now_seconds, char out_error[32]);

/* Record an error without losing last-good data */
void meter_state_record_error(meter_state_t *state, const char *error_code, const char *reason);

/* Update stale status based on current time */
void meter_state_update_stale(meter_state_t *state, int64_t now_seconds);

/* Cycle screen mode on BOOT press with 300ms debounce */
bool meter_state_cycle_screen(meter_state_t *state, uint32_t now_ms);

/* Set display orientation (from IMU) */
void meter_state_set_orientation(meter_state_t *state, display_orientation_t orientation);

#ifdef __cplusplus
}
#endif

#endif /* METER_STATE_H */
