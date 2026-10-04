#pragma once
#include <stddef.h>
#include <stdint.h>

#include "meter_parser.h"

#ifdef __cplusplus
extern "C" {
#endif

#define METER_STALE_SECONDS 300u
#define METER_ERROR_MAX 40u

typedef struct {
    int has_seq;
    uint32_t seq;
    char sent_at[METER_SENT_AT_MAX];
    /* Monotonic receive time in seconds (esp_timer / host test clock). */
    uint64_t received_monotonic_s;
    int stale; /* receive-age >= 300 s */
    int has_payload;
    char last_good_crc[9];
    char last_error[METER_ERROR_MAX];
} meter_receiver_t;

void meter_receiver_init(meter_receiver_t *r);

/* Explicit operator reset only (e.g. re-provisioning an empty receiver).
 * Never called on disconnect/stale/new sent_at. */
void meter_receiver_reset(meter_receiver_t *r);

/* Update the receive-age stale flag against now_monotonic_s. */
void meter_receiver_update_stale(meter_receiver_t *r, uint64_t now_monotonic_s);

/* Accept one LF-terminated line. reference_time may be NULL (no future check).
 * Returns METER_FRAME_OK on accept; otherwise the rejection code. On reject
 * the previous last-good state is preserved and last_error is set. */
int meter_receiver_accept(meter_receiver_t *r, const uint8_t *line, size_t len,
                          uint64_t now_monotonic_s, const char *reference_time);

#ifdef __cplusplus
}
#endif
