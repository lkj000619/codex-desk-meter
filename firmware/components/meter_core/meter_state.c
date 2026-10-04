#include "meter_state.h"

#include <stdio.h>
#include <string.h>

void meter_receiver_init(meter_receiver_t *r) {
    memset(r, 0, sizeof *r);
    r->last_error[0] = '\0';
    r->last_good_crc[0] = '\0';
}

void meter_receiver_reset(meter_receiver_t *r) {
    meter_receiver_init(r);
}

void meter_receiver_update_stale(meter_receiver_t *r, uint64_t now_monotonic_s) {
    if (!r->has_payload) {
        r->stale = 0;
        return;
    }
    uint64_t age = now_monotonic_s >= r->received_monotonic_s
                       ? now_monotonic_s - r->received_monotonic_s
                       : 0;
    r->stale = age >= METER_STALE_SECONDS;
}

static void set_error(meter_receiver_t *r, int code) {
    snprintf(r->last_error, sizeof r->last_error, "%s", meter_frame_code_str(code));
}

int meter_receiver_accept(meter_receiver_t *r, const uint8_t *line, size_t len,
                          uint64_t now_monotonic_s, const char *reference_time) {
    meter_receiver_update_stale(r, now_monotonic_s);
    meter_frame_info_t info;
    int rc = meter_frame_check(line, len, &info);
    if (rc != METER_FRAME_OK) {
        set_error(r, rc);
        return rc;
    }
    if (reference_time && meter_sent_at_is_future(info.sent_at, reference_time)) {
        set_error(r, METER_FRAME_TIMESTAMP_INVALID);
        return METER_FRAME_TIMESTAMP_INVALID;
    }
    if (r->has_seq) {
        if (info.sequence == r->seq) {
            set_error(r, METER_FRAME_SEQUENCE_INVALID);
            snprintf(r->last_error, sizeof r->last_error, "%s", "DUPLICATE_SEQUENCE");
            return METER_FRAME_SEQUENCE_INVALID;
        }
        if (!meter_sequence_is_newer(info.sequence, r->seq)) {
            set_error(r, METER_FRAME_SEQUENCE_INVALID);
            snprintf(r->last_error, sizeof r->last_error, "%s", "OUT_OF_ORDER_SEQUENCE");
            return METER_FRAME_SEQUENCE_INVALID;
        }
    }
    r->has_seq = 1;
    r->seq = info.sequence;
    snprintf(r->sent_at, sizeof r->sent_at, "%s", info.sent_at);
    r->received_monotonic_s = now_monotonic_s;
    r->has_payload = 1;
    memcpy(r->last_good_crc, info.crc, 9);
    r->last_error[0] = '\0';
    uint64_t age = 0; /* just received */
    (void)age;
    meter_receiver_update_stale(r, now_monotonic_s);
    /* A fresh frame clears receive-age staleness by construction (age 0),
     * but never clears a source-age staleness owned by the payload itself. */
    return METER_FRAME_OK;
}
