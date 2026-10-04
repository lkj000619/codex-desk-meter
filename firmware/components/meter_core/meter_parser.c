#include "meter_parser.h"
#include "meter_crc32.h"

#include <ctype.h>
#include <stdio.h>
#include <string.h>

const char *meter_frame_code_str(int code) {
    switch (code) {
        case METER_FRAME_OK: return "OK";
        case METER_FRAME_TRUNCATED: return "FRAME_TRUNCATED";
        case METER_FRAME_NEWLINE_INVALID: return "FRAME_NEWLINE_INVALID";
        case METER_FRAME_OVERSIZED: return "FRAME_OVERSIZED";
        case METER_FRAME_INVALID_UTF8: return "INVALID_UTF8";
        case METER_FRAME_MALFORMED: return "MALFORMED_JSON";
        case METER_FRAME_UNSUPPORTED_VERSION: return "UNSUPPORTED_VERSION";
        case METER_FRAME_SCHEMA_INVALID: return "FRAME_SCHEMA_INVALID";
        case METER_FRAME_CRC_MISMATCH: return "CRC_MISMATCH";
        case METER_FRAME_TIMESTAMP_INVALID: return "TIMESTAMP_INVALID";
        case METER_FRAME_SEQUENCE_INVALID: return "SEQUENCE_INVALID";
        default: return "UNKNOWN";
    }
}

int meter_sequence_is_newer(uint32_t candidate, uint32_t current) {
    uint32_t distance = candidate - current;
    return distance != 0 && distance < 0x80000000u;
}

int meter_sent_at_shape_ok(const char *s) {
    /* Accept YYYY-MM-DDTHH:MM:SS[Z or +/-HH:MM]. Minimal structural check. */
    if (!s) {
        return 0;
    }
    size_t n = strlen(s);
    if (n < 20 || n >= METER_SENT_AT_MAX) {
        return 0;
    }
    for (int i = 0; i < 4; i++) {
        if (!isdigit((unsigned char)s[i])) {
            return 0;
        }
    }
    if (s[4] != '-' || s[7] != '-') {
        return 0;
    }
    if (s[10] != 'T' && s[10] != 't') {
        return 0;
    }
    if (s[13] != ':' || s[16] != ':') {
        return 0;
    }
    for (int i = 5; i < 19; i++) {
        if (i == 7 || i == 10 || i == 13 || i == 16) {
            continue;
        }
        if (i == 4 || i == 7) {
            continue;
        }
        if (!isdigit((unsigned char)s[i])) {
            return 0;
        }
    }
    return 1;
}

int meter_sent_at_is_future(const char *sent_at, const char *reference_time) {
    if (!sent_at || !reference_time) {
        return 0;
    }
    return strcmp(sent_at, reference_time) > 0;
}

static int utf8_ok(const uint8_t *p, size_t len) {
    size_t i = 0;
    while (i < len) {
        uint8_t c = p[i];
        size_t extra = 0;
        if ((c & 0x80) == 0) {
            i += 1;
            continue;
        } else if ((c & 0xE0) == 0xC0) {
            extra = 1;
            if (c < 0xC2) {
                return 0;
            }
        } else if ((c & 0xF0) == 0xE0) {
            extra = 2;
        } else if ((c & 0xF8) == 0xF0) {
            extra = 3;
            if (c > 0xF4) {
                return 0;
            }
        } else {
            return 0;
        }
        if (i + extra >= len) {
            return 0;
        }
        for (size_t k = 1; k <= extra; k++) {
            if ((p[i + k] & 0xC0) != 0x80) {
                return 0;
            }
        }
        i += 1 + extra;
    }
    return 1;
}

static const uint8_t *find_token(const uint8_t *beg, const uint8_t *end, const char *tok) {
    size_t n = strlen(tok);
    if (n == 0 || (size_t)(end - beg) < n) {
        return NULL;
    }
    for (const uint8_t *p = beg; p + n <= end; p++) {
        if (memcmp(p, tok, n) == 0) {
            return p;
        }
    }
    return NULL;
}

int meter_json_find_string(const uint8_t *beg, const uint8_t *end,
                           const char *key, char *out, size_t out_sz) {
    char pat[96];
    snprintf(pat, sizeof pat, "\"%s\"", key);
    const uint8_t *k = find_token(beg, end, pat);
    if (!k || out_sz == 0) {
        return 0;
    }
    const uint8_t *p = k + strlen(pat);
    while (p < end && (*p == ' ' || *p == '\t' || *p == '\r')) {
        p++;
    }
    if (p >= end || *p != ':') {
        return 0;
    }
    p++;
    while (p < end && (*p == ' ' || *p == '\t')) {
        p++;
    }
    if (p >= end || *p != '"') {
        return 0;
    }
    p++;
    size_t o = 0;
    while (p < end && *p != '"') {
        if (*p == '\\') {
            p++;
            if (p >= end) {
                return 0;
            }
            char esc = (char)*p++;
            char c = esc;
            if (esc == 'n') {
                c = '\n';
            } else if (esc == 't') {
                c = '\t';
            } else if (esc == 'u') {
                /* Keep raw: copy 'u' plus 4 hex as-is marker. */
                if (o + 1 < out_sz) {
                    out[o++] = 'u';
                }
                for (int i = 0; i < 4 && p < end; i++) {
                    if (o + 1 < out_sz) {
                        out[o++] = (char)*p;
                    }
                    p++;
                }
                continue;
            }
            if (o + 1 < out_sz) {
                out[o++] = c;
            }
        } else {
            if (o + 1 < out_sz) {
                out[o++] = (char)*p;
            }
            p++;
        }
    }
    if (p >= end) {
        return 0;
    }
    out[o] = '\0';
    return 1;
}

int meter_json_find_number(const uint8_t *beg, const uint8_t *end,
                           const char *key, double *num, int *is_null) {
    char pat[96];
    snprintf(pat, sizeof pat, "\"%s\"", key);
    const uint8_t *k = find_token(beg, end, pat);
    if (!k) {
        return 0;
    }
    const uint8_t *p = k + strlen(pat);
    while (p < end && (*p == ' ' || *p == '\t')) {
        p++;
    }
    if (p >= end || *p != ':') {
        return 0;
    }
    p++;
    while (p < end && (*p == ' ' || *p == '\t')) {
        p++;
    }
    if (p >= end) {
        return 0;
    }
    if ((size_t)(end - p) >= 4 && memcmp(p, "null", 4) == 0) {
        if (is_null) {
            *is_null = 1;
        }
        return 1;
    }
    /* Reject NaN/Infinity explicitly. */
    if ((size_t)(end - p) >= 3 && (memcmp(p, "NaN", 3) == 0 || memcmp(p, "Inf", 3) == 0)) {
        return 0;
    }
    char buf[64];
    size_t o = 0;
    const uint8_t *q = p;
    if (q < end && (*q == '-' || *q == '+')) {
        if (o + 1 < sizeof buf) {
            buf[o++] = (char)*q;
        }
        q++;
    }
    int digits = 0;
    while (q < end && (isdigit((unsigned char)*q) || *q == '.' || *q == 'e' || *q == 'E' || *q == '-' || *q == '+')) {
        if (isdigit((unsigned char)*q)) {
            digits++;
        }
        if (o + 1 < sizeof buf) {
            buf[o++] = (char)*q;
        }
        q++;
    }
    if (!digits) {
        return 0;
    }
    buf[o] = '\0';
    /* Manual conversion to avoid locale/strtod dependency surprises. */
    double v = 0;
    if (sscanf(buf, "%lf", &v) != 1) {
        return 0;
    }
    if (num) {
        *num = v;
    }
    if (is_null) {
        *is_null = 0;
    }
    return 1;
}

static int parse_sequence(const uint8_t *beg, const uint8_t *end, uint32_t *out) {
    double v = 0;
    int is_null = 0;
    if (!meter_json_find_number(beg, end, "sequence", &v, &is_null) || is_null) {
        return 0;
    }
    if (v < 0 || v > 4294967295.0 || v != (double)(uint32_t)v) {
        return 0;
    }
    /* Reject fractional forms like 1.5: rescan raw token for '.'/'e'. */
    char pat[] = "\"sequence\"";
    const uint8_t *k = find_token(beg, end, pat);
    if (!k) {
        return 0;
    }
    const uint8_t *p = k + sizeof(pat) - 1;
    while (p < end && (*p == ' ' || *p == '\t')) {
        p++;
    }
    if (p >= end || *p != ':') {
        return 0;
    }
    p++;
    while (p < end && (*p == ' ' || *p == '\t')) {
        p++;
    }
    const uint8_t *q = p;
    while (q < end && (isdigit((unsigned char)*q))) {
        q++;
    }
    if (q < end && (*q == '.' || *q == 'e' || *q == 'E')) {
        return 0;
    }
    *out = (uint32_t)v;
    return 1;
}

int meter_frame_check(const uint8_t *line, size_t line_len, meter_frame_info_t *info) {
    if (info) {
        memset(info, 0, sizeof *info);
    }
    if (line_len == 0 || line_len > METER_MAX_LINE) {
        return METER_FRAME_OVERSIZED;
    }
    if (line[line_len - 1] != '\n') {
        return METER_FRAME_TRUNCATED;
    }
    size_t body_len = line_len - 1;
    const uint8_t *body = line;
    const uint8_t *body_end = line + body_len;
    for (size_t i = 0; i < body_len; i++) {
        if (body[i] == '\n') {
            return METER_FRAME_NEWLINE_INVALID;
        }
        if (body[i] == '\r') {
            return METER_FRAME_NEWLINE_INVALID;
        }
    }
    if (!utf8_ok(body, body_len)) {
        return METER_FRAME_INVALID_UTF8;
    }
    /* Trim surrounding spaces (canonical has none, be liberal on edges only). */
    const uint8_t *beg = body;
    const uint8_t *end = body_end;
    while (beg < end && (*beg == ' ' || *beg == '\t')) {
        beg++;
    }
    while (end > beg && (end[-1] == ' ' || end[-1] == '\t')) {
        end--;
    }
    if (end - beg < 2 || beg[0] != '{' || end[-1] != '}') {
        return METER_FRAME_MALFORMED;
    }
    char protocol[16] = {0};
    if (!meter_json_find_string(beg, end, "protocol", protocol, sizeof protocol)) {
        return METER_FRAME_SCHEMA_INVALID;
    }
    if (strcmp(protocol, "cdm/1") != 0) {
        return METER_FRAME_UNSUPPORTED_VERSION;
    }
    uint32_t seq = 0;
    if (!parse_sequence(beg, end, &seq)) {
        return METER_FRAME_SEQUENCE_INVALID;
    }
    char sent_at[METER_SENT_AT_MAX] = {0};
    if (!meter_json_find_string(beg, end, "sent_at", sent_at, sizeof sent_at)) {
        return METER_FRAME_TIMESTAMP_INVALID;
    }
    if (!meter_sent_at_shape_ok(sent_at)) {
        return METER_FRAME_TIMESTAMP_INVALID;
    }
    if (!find_token(beg, end, "\"payload\"") || !find_token(beg, end, "\"usage\"") ||
        !find_token(beg, end, "\"global_resets\"")) {
        return METER_FRAME_SCHEMA_INVALID;
    }
    char algo[16] = {0};
    char value[16] = {0};
    if (!meter_json_find_string(beg, end, "algorithm", algo, sizeof algo) ||
        !meter_json_find_string(beg, end, "value", value, sizeof value)) {
        return METER_FRAME_SCHEMA_INVALID;
    }
    if (strcmp(algo, "crc32") != 0) {
        return METER_FRAME_SCHEMA_INVALID;
    }
    if (strlen(value) != 8) {
        return METER_FRAME_SCHEMA_INVALID;
    }
    for (int i = 0; i < 8; i++) {
        if (!isxdigit((unsigned char)value[i]) || islower((unsigned char)value[i])) {
            /* Allow only 0-9A-F. Lowercase hex is a schema violation. */
            if (!isdigit((unsigned char)value[i]) && !(value[i] >= 'A' && value[i] <= 'F')) {
                return METER_FRAME_SCHEMA_INVALID;
            }
        }
    }
    /* Derive the unsigned envelope: canonical order puts integrity first, so the
     * unsigned bytes are "{" + bytes from "\"payload\":" through the final "}". */
    const uint8_t *pay = find_token(beg, end, "\"payload\"");
    if (!pay) {
        return METER_FRAME_SCHEMA_INVALID;
    }
    /* end[-1] is '}'. Unsigned = '{' + [pay, end-1). */
    size_t tail_len = (size_t)((end - 1) - pay);
    size_t unsigned_len = 1 + tail_len + 1;
    if (unsigned_len > METER_MAX_LINE) {
        return METER_FRAME_OVERSIZED;
    }
    /* CRC over unsigned envelope. Stream without allocating: hash '{', tail, '}'. */
    uint8_t open_b = '{';
    uint8_t close_b = '}';
    /* Compute incrementally to avoid a 64K stack buffer. */
    extern uint32_t meter_crc32(const uint8_t *, size_t);
    /* Fall back to a small local incremental implementation. */
    uint32_t crc = 0xFFFFFFFFu;
    /* Reuse table via meter_crc32 of chunks is not incremental; implement here. */
    static uint32_t table[256];
    static int table_ok = 0;
    if (!table_ok) {
        for (uint32_t i = 0; i < 256; i++) {
            uint32_t c = i;
            for (int k = 0; k < 8; k++) {
                c = (c & 1) ? (0xEDB88320u ^ (c >> 1)) : (c >> 1);
            }
            table[i] = c;
        }
        table_ok = 1;
    }
#define CRC_BYTE(b) crc = table[(crc ^ (b)) & 0xFF] ^ (crc >> 8)
    CRC_BYTE(open_b);
    for (size_t i = 0; i < tail_len; i++) {
        CRC_BYTE(pay[i]);
    }
    CRC_BYTE(close_b);
#undef CRC_BYTE
    crc ^= 0xFFFFFFFFu;
    char expect[9];
    static const char *hexd = "0123456789ABCDEF";
    for (int i = 7; i >= 0; i--) {
        expect[i] = hexd[crc & 0xF];
        crc >>= 4;
    }
    expect[8] = '\0';
    if (memcmp(expect, value, 8) != 0) {
        return METER_FRAME_CRC_MISMATCH;
    }
    if (info) {
        info->code = METER_FRAME_OK;
        info->sequence = seq;
        snprintf(info->sent_at, sizeof info->sent_at, "%s", sent_at);
        memcpy(info->crc, value, 8);
        info->crc[8] = '\0';
        info->unsigned_off = (size_t)(pay - line);
        info->unsigned_len = unsigned_len;
    }
    return METER_FRAME_OK;
}
