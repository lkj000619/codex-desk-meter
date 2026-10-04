#pragma once
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define METER_MAX_LINE 65536u
#define METER_SENT_AT_MAX 32u
#define METER_CODE_MAX 40u

typedef enum {
    METER_FRAME_OK = 0,
    METER_FRAME_TRUNCATED = 1,      /* missing single trailing LF */
    METER_FRAME_NEWLINE_INVALID = 2,/* extra LF / CRLF / blank line */
    METER_FRAME_OVERSIZED = 3,
    METER_FRAME_INVALID_UTF8 = 4,
    METER_FRAME_MALFORMED = 5,      /* not a JSON object with required keys */
    METER_FRAME_UNSUPPORTED_VERSION = 6,
    METER_FRAME_SCHEMA_INVALID = 7,
    METER_FRAME_CRC_MISMATCH = 8,
    METER_FRAME_TIMESTAMP_INVALID = 9,
    METER_FRAME_SEQUENCE_INVALID = 10
} meter_frame_code_t;

typedef struct {
    meter_frame_code_t code;
    uint32_t sequence;
    char sent_at[METER_SENT_AT_MAX];
    char crc[9];
    /* Offsets into the line body (without trailing LF). */
    size_t unsigned_off; /* offset of "{\"payload\":" unsigned envelope start ('{') */
    size_t unsigned_len; /* length of unsigned envelope bytes */
} meter_frame_info_t;

/* Validate one LF-terminated cdm/1 line. line_len includes the trailing LF.
 * Returns METER_FRAME_OK (0) on success and fills info. */
int meter_frame_check(const uint8_t *line, size_t line_len, meter_frame_info_t *info);

/* Human readable stable code string for logs/status screen. */
const char *meter_frame_code_str(int code);

/* Sequence novelty: true only when 0 < (candidate-current) mod 2^32 < 2^31. */
int meter_sequence_is_newer(uint32_t candidate, uint32_t current);

/* Minimal RFC3339 sanity for "sent_at" (YYYY-MM-DDTHH:MM:SS with timezone).
 * Returns 1 when the shape is acceptable, 0 otherwise. */
int meter_sent_at_shape_ok(const char *s);

/* Lexicographic future check for UTC "Z" timestamps in fixed format.
 * Returns 1 when sent_at > reference_time, else 0. Both must be NUL strings. */
int meter_sent_at_is_future(const char *sent_at, const char *reference_time);

/* Find a JSON string value for "key" (key without quotes) inside [beg, end).
 * Copies up to out_sz-1 chars. Returns 1 on found, 0 otherwise. */
int meter_json_find_string(const uint8_t *beg, const uint8_t *end,
                           const char *key, char *out, size_t out_sz);

/* Find a JSON number (or null) for "key". Returns 1 and sets *is_null / *num. */
int meter_json_find_number(const uint8_t *beg, const uint8_t *end,
                           const char *key, double *num, int *is_null);

#ifdef __cplusplus
}
#endif
