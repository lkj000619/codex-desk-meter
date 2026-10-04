#ifndef METER_PARSER_H
#define METER_PARSER_H

#include "meter_types.h"
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Parse an RFC3339 timestamp string to UTC unix timestamp in seconds.
 * Returns true if valid RFC3339 with timezone, false otherwise. */
bool meter_parse_rfc3339(const char *str, int64_t *out_seconds);

/* Format UTC unix timestamp in seconds to RFC3339 "YYYY-MM-DDTHH:MM:SSZ". */
void meter_format_rfc3339(int64_t seconds, char *out_str, size_t max_len);

/* Check if candidate sequence is newer than current sequence according to cdm/1:
 * 0 < (candidate - current) mod 2^32 < 2^31. */
bool meter_sequence_is_newer(uint32_t candidate, uint32_t current);

/* Verify CRC32 on canonical cdm/1 JSON frame line.
 * Returns true if valid CRC and canonical integrity placement, false otherwise. */
bool meter_verify_frame_crc(const char *raw_line, size_t line_len, char out_expected_crc[9], char out_actual_crc[9]);

/* Parse raw cdm/1 frame line (including trailing '\n').
 * Validates protocol, sequence, CRC, timestamps, snapshots, and global resets. */
bool meter_parse_frame(const char *raw_line, size_t line_len, meter_frame_t *out_frame, char out_error_code[32]);

/* Legacy adapter event structures for scripts/evaluate-product.py seam */
typedef struct {
    char now[METER_MAX_STRING_LEN];
    int64_t now_seconds;
    char *body_raw;         /* Raw JSON string or NULL */
    char error[32];         /* "dns", "tls", "http_500", or empty */
} meter_legacy_event_t;

typedef struct {
    char source[METER_MAX_STRING_LEN];
    meter_legacy_event_t events[8];
    size_t event_count;
} meter_legacy_request_t;

/* Parse legacy adapter stdin JSON {source, events:[{now, body, error}]}. */
bool meter_parse_legacy_request(const char *json_str, meter_legacy_request_t *out_req);
void meter_free_legacy_request(meter_legacy_request_t *req);

#ifdef __cplusplus
}
#endif

#endif /* METER_PARSER_H */
