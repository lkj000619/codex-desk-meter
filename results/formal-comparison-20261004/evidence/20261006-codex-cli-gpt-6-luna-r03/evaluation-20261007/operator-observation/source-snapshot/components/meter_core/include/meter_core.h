#ifndef METER_CORE_H
#define METER_CORE_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define METER_MAX_FRAME_BYTES 65536u
#define METER_STALE_AFTER_SECONDS 300u

typedef struct {
    bool has_sequence;
    bool has_good_frame;
    uint32_t sequence;
    uint64_t accepted_at_ms;
    bool receive_stale;
    char last_error[40];
    char *last_good_line;
    size_t last_good_length;
} meter_receiver_t;

void meter_receiver_init(meter_receiver_t *receiver);
void meter_receiver_deinit(meter_receiver_t *receiver);
bool meter_receiver_receive(meter_receiver_t *receiver,
                            const uint8_t *line,
                            size_t length,
                            uint64_t monotonic_ms);
void meter_receiver_poll(meter_receiver_t *receiver, uint64_t monotonic_ms);
uint32_t meter_crc32(const uint8_t *bytes, size_t length);
bool meter_sequence_is_newer(uint32_t candidate, uint32_t current);
bool meter_timestamp_delta_seconds(const char *newer,
                                   const char *older,
                                   int64_t *delta_seconds);
bool meter_source_is_stale(const char *frame_sent_at,
                           const char *source_observed_at,
                           uint64_t frame_age_ms);

#ifdef __cplusplus
}
#endif

#endif
