#include "meter_state.h"
#include "meter_parser.h"
#include <string.h>

void meter_state_init(meter_state_t *state)
{
    if (!state) return;
    memset(state, 0, sizeof(*state));
    state->has_sequence = false;
    state->current_sequence = 0;
    state->screen_mode = SCREEN_DASHBOARD;
    state->orientation = ORIENTATION_LANDSCAPE_NORMAL;
}

bool meter_state_process_frame(meter_state_t *state, const meter_frame_t *frame, int64_t now_seconds, char out_error[32])
{
    if (!state || !frame) return false;

    /* Sequence number validation */
    if (state->has_sequence) {
        if (frame->sequence == state->current_sequence) {
            strncpy(out_error, "DUPLICATE_SEQUENCE", 31);
            meter_state_record_error(state, "DUPLICATE_SEQUENCE", "duplicate sequence");
            return false;
        }
        if (!meter_sequence_is_newer(frame->sequence, state->current_sequence)) {
            strncpy(out_error, "OUT_OF_ORDER_SEQUENCE", 31);
            meter_state_record_error(state, "OUT_OF_ORDER_SEQUENCE", "out-of-order sequence");
            return false;
        }
    }

    /* Future sent_at check */
    int64_t sent_sec = 0;
    if (meter_parse_rfc3339(frame->sent_at, &sent_sec)) {
        if (now_seconds > 0 && sent_sec > now_seconds) {
            strncpy(out_error, "FUTURE_TIMESTAMP", 31);
            meter_state_record_error(state, "FUTURE_TIMESTAMP", "sent_at is in the future");
            return false;
        }
    }

    /* Accept sequence */
    state->has_sequence = true;
    state->current_sequence = frame->sequence;
    state->last_receive_time = now_seconds;
    strncpy(state->last_receive_stamp, frame->sent_at, sizeof(state->last_receive_stamp)-1);

    /* Update last-good usage */
    state->usage_count = 0;
    for (size_t i = 0; i < frame->usage_count && i < METER_MAX_SNAPSHOTS; ++i) {
        state->usage[state->usage_count++] = frame->usage[i];
    }

    /* Update last-good global resets */
    state->global_reset_count = 0;
    for (size_t i = 0; i < frame->global_reset_count && i < METER_MAX_GLOBAL_RESETS; ++i) {
        state->global_resets[state->global_reset_count++] = frame->global_resets[i];
    }

    state->last_good_time = (sent_sec > 0) ? sent_sec : now_seconds;
    strncpy(state->last_good_stamp, frame->sent_at, sizeof(state->last_good_stamp)-1);

    /* Clear error on valid frame */
    state->has_error = false;
    state->last_error_code[0] = '\0';
    state->last_error_reason[0] = '\0';

    meter_state_update_stale(state, now_seconds);
    return true;
}

void meter_state_record_error(meter_state_t *state, const char *error_code, const char *reason)
{
    if (!state) return;
    state->has_error = true;
    if (error_code) strncpy(state->last_error_code, error_code, sizeof(state->last_error_code)-1);
    if (reason) strncpy(state->last_error_reason, reason, sizeof(state->last_error_reason)-1);
}

void meter_state_update_stale(meter_state_t *state, int64_t now_seconds)
{
    if (!state || now_seconds <= 0) return;

    /* Check receiver-age vs last frame receive time */
    if (state->last_receive_time > 0) {
        int64_t recv_age = now_seconds - state->last_receive_time;
        state->is_stale = (recv_age >= METER_STALE_THRESHOLD_SECONDS);
    } else {
        state->is_stale = false;
    }

    /* Also evaluate source-age on each individual snapshot */
    for (size_t i = 0; i < state->usage_count; ++i) {
        meter_snapshot_t *snap = &state->usage[i];
        if (snap->observed_at[0] != '\0') {
            int64_t obs_sec = 0;
            if (meter_parse_rfc3339(snap->observed_at, &obs_sec)) {
                int64_t src_age = now_seconds - obs_sec;
                if (src_age >= METER_STALE_THRESHOLD_SECONDS) {
                    snap->stale = true;
                    if (snap->status == SNAPSHOT_STATUS_AVAILABLE) {
                        snap->status = SNAPSHOT_STATUS_STALE;
                    }
                }
            }
        }
    }

    /* Global reset stale */
    for (size_t i = 0; i < state->global_reset_count; ++i) {
        meter_global_reset_t *gr = &state->global_resets[i];
        if (gr->captured_at[0] != '\0') {
            int64_t cap_sec = 0;
            if (meter_parse_rfc3339(gr->captured_at, &cap_sec)) {
                int64_t cap_age = now_seconds - cap_sec;
                if (cap_age >= METER_STALE_THRESHOLD_SECONDS) {
                    gr->stale = true;
                }
            }
        }
    }
}

bool meter_state_cycle_screen(meter_state_t *state, uint32_t now_ms)
{
    if (!state) return false;
    if (now_ms - state->last_screen_switch_ms < 300) {
        return false; /* Debounce 300ms */
    }
    state->screen_mode = (screen_mode_t)((state->screen_mode + 1) % SCREEN_MAX_COUNT);
    state->last_screen_switch_ms = now_ms;
    return true;
}

void meter_state_set_orientation(meter_state_t *state, display_orientation_t orientation)
{
    if (!state) return;
    state->orientation = orientation;
}
