/* Host test for the production cdm/1 frame parser (meter_parser.c +
 * meter_crc32.c). Covers canonical framing, CRC, version, size, newline,
 * UTF-8, truncation, and the uint32 sequence novelty rule incl. wrap. */
#include <assert.h>
#include <stdio.h>
#include <string.h>

#include "meter_crc32.h"
#include "meter_parser.h"

static int failures;

#define CHECK(cond)                                                            \
    do {                                                                       \
        if (!(cond)) {                                                         \
            printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond);              \
            failures++;                                                        \
        }                                                                      \
    } while (0)

/* Build a canonical frame line with a correct CRC using the production CRC. */
static size_t build_frame(char *out, size_t cap, unsigned seq, const char *sent_at,
                          const char *usage, const char *resets) {
    char unsigned_buf[8192];
    int n = snprintf(unsigned_buf, sizeof unsigned_buf,
                     "{\"payload\":{\"global_resets\":[%s],\"usage\":[%s]},"
                     "\"protocol\":\"cdm/1\",\"sent_at\":\"%s\",\"sequence\":%u}",
                     resets, usage, sent_at, seq);
    assert(n > 0 && (size_t)n < sizeof unsigned_buf);
    char hex[9];
    meter_crc32_hex((const unsigned char *)unsigned_buf, (size_t)n, hex);
    int m = snprintf(out, cap,
                     "{\"integrity\":{\"algorithm\":\"crc32\",\"value\":\"%s\"},"
                     "\"payload\":{\"global_resets\":[%s],\"usage\":[%s]},"
                     "\"protocol\":\"cdm/1\",\"sent_at\":\"%s\",\"sequence\":%u}\n",
                     hex, resets, usage, sent_at, seq);
    assert(m > 0 && (size_t)m < cap);
    return (size_t)m;
}

int main(void) {
    /* Universal CRC golden (zlib reference). */
    CHECK(meter_crc32((const unsigned char *)"123456789", 9) == 0xCBF43926u);
    char hex[9];
    meter_crc32_hex((const unsigned char *)"123456789", 9, hex);
    CHECK(strcmp(hex, "CBF43926") == 0);

    char line[8192];
    size_t len = build_frame(line, sizeof line, 7, "2026-09-10T00:04:59Z", "", "");
    meter_frame_info_t info;
    CHECK(meter_frame_check((const unsigned char *)line, len, &info) == METER_FRAME_OK);
    CHECK(info.sequence == 7);
    CHECK(strcmp(info.sent_at, "2026-09-10T00:04:59Z") == 0);

    /* Wrap-around: 2^32-1 -> 0 is accepted at the sequence layer. */
    CHECK(meter_sequence_is_newer(0, 4294967295u) == 1);
    CHECK(meter_sequence_is_newer(7, 7) == 0);
    CHECK(meter_sequence_is_newer(6, 7) == 0);
    CHECK(meter_sequence_is_newer(7 + 0x80000000u, 7) == 0); /* half-range reject */
    CHECK(meter_sequence_is_newer(8, 7) == 1);

    /* Missing LF -> truncated. */
    CHECK(meter_frame_check((const unsigned char *)line, len - 1, NULL) ==
          METER_FRAME_TRUNCATED);
    /* Extra LF -> newline invalid. */
    {
        char two[8192];
        memcpy(two, line, len);
        two[len] = '\n';
        CHECK(meter_frame_check((const unsigned char *)two, len + 1, NULL) ==
              METER_FRAME_NEWLINE_INVALID);
    }
    /* CRLF -> newline invalid. */
    {
        char cr[8192];
        memcpy(cr, line, len);
        cr[len - 1] = '\r';
        cr[len] = '\n';
        CHECK(meter_frame_check((const unsigned char *)cr, len + 1, NULL) ==
              METER_FRAME_NEWLINE_INVALID);
    }
    /* Mutating the payload region breaks the CRC (integrity covers the
     * unsigned envelope; the integrity field itself is not covered). */
    {
        char pretty[8192];
        size_t plen = build_frame(pretty, sizeof pretty, 7, "2026-09-10T00:04:59Z", "", "");
        char *q = strstr(pretty, "2026-09-10T00:04:59Z");
        assert(q != NULL);
        q[5] = (q[5] == '0') ? '1' : '0';
        CHECK(meter_frame_check((const unsigned char *)pretty, plen, NULL) ==
              METER_FRAME_CRC_MISMATCH);
    }
    /* Flipped CRC hex nibble (first hex char of the value). */
    {
        char bad[8192];
        memcpy(bad, line, len);
        char *q = strstr(bad, "\"value\":\"");
        assert(q != NULL);
        q[9] = (q[9] == 'A') ? 'B' : 'A';
        CHECK(meter_frame_check((const unsigned char *)bad, len, NULL) ==
              METER_FRAME_CRC_MISMATCH);
    }
    /* Wrong protocol. */
    {
        char *p = strstr(line, "cdm/1");
        char saved = *p;
        (void)saved;
        char mod[8192];
        memcpy(mod, line, len);
        char *q = strstr(mod, "cdm/1");
        memcpy(q, "cdm/2", 5);
        /* CRC now also wrong, but version is checked first. */
        CHECK(meter_frame_check((const unsigned char *)mod, len, NULL) ==
              METER_FRAME_UNSUPPORTED_VERSION);
    }
    /* Fractional sequence rejected (valid CRC, integer check first). */
    {
        const char *unsigned_fmt =
            "{\"payload\":{\"global_resets\":[],\"usage\":[]},"
            "\"protocol\":\"cdm/1\",\"sent_at\":\"2026-09-10T00:04:59Z\","
            "\"sequence\":7.5}";
        char hex2[9];
        meter_crc32_hex((const unsigned char *)unsigned_fmt, strlen(unsigned_fmt), hex2);
        char frac[8192];
        int m = snprintf(frac, sizeof frac,
                         "{\"integrity\":{\"algorithm\":\"crc32\",\"value\":\"%s\"},"
                         "%s\n",
                         hex2, unsigned_fmt + 1);
        /* unsigned_fmt+1 strips the leading '{'; re-add via the prefix above. */
        assert(m > 0 && (size_t)m < sizeof frac);
        meter_frame_info_t fi;
        int rc = meter_frame_check((const unsigned char *)frac, (size_t)m, &fi);
        CHECK(rc == METER_FRAME_SEQUENCE_INVALID);
    }
    /* Invalid UTF-8. */
    {
        char bad8[8192];
        size_t blen = build_frame(bad8, sizeof bad8, 9, "2026-09-10T00:04:59Z", "", "");
        bad8[10] = (char)0xFF;
        int rc = meter_frame_check((const unsigned char *)bad8, blen, NULL);
        CHECK(rc == METER_FRAME_INVALID_UTF8 || rc == METER_FRAME_CRC_MISMATCH);
    }
    /* Lowercase hex CRC rejected by schema. */
    {
        char lower[8192];
        size_t llen = build_frame(lower, sizeof lower, 11, "2026-09-10T00:04:59Z", "", "");
        for (size_t i = 0; i < llen; i++) {
            if (lower[i] >= 'A' && lower[i] <= 'F') {
                lower[i] = (char)(lower[i] - 'A' + 'a');
                break;
            }
        }
        int rc = meter_frame_check((const unsigned char *)lower, llen, NULL);
        CHECK(rc == METER_FRAME_SCHEMA_INVALID || rc == METER_FRAME_CRC_MISMATCH);
    }
    /* Oversized. */
    CHECK(meter_frame_check((const unsigned char *)line, METER_MAX_LINE + 1, NULL) ==
          METER_FRAME_OVERSIZED);

    /* sent_at shape + future comparison. */
    CHECK(meter_sent_at_shape_ok("2026-09-10T00:04:59Z") == 1);
    CHECK(meter_sent_at_shape_ok("not-a-time") == 0);
    CHECK(meter_sent_at_is_future("2026-09-10T00:05:00Z", "2026-09-10T00:04:59Z") == 1);
    CHECK(meter_sent_at_is_future("2026-09-10T00:04:59Z", "2026-09-10T00:04:59Z") == 0);

    if (failures == 0) {
        printf("test_meter_parser: PASS\n");
        return 0;
    }
    printf("test_meter_parser: %d FAILURES\n", failures);
    return 1;
}
