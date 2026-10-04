/* Host test for the production receiver state (meter_state.c):
 * accept/dup/reverse/wrap, last-good preservation, receive-age staleness
 * at the 0/299/300 s boundary, and no seq reset on stale/disconnect. */
#include <assert.h>
#include <stdio.h>
#include <string.h>

#include "meter_crc32.h"
#include "meter_parser.h"
#include "meter_state.h"

static int failures;

#define CHECK(cond)                                                            \
    do {                                                                       \
        if (!(cond)) {                                                         \
            printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond);              \
            failures++;                                                        \
        }                                                                      \
    } while (0)

static size_t build_frame(char *out, size_t cap, unsigned seq, const char *sent_at) {
    char unsigned_buf[4096];
    int n = snprintf(unsigned_buf, sizeof unsigned_buf,
                     "{\"payload\":{\"global_resets\":[],\"usage\":[]},"
                     "\"protocol\":\"cdm/1\",\"sent_at\":\"%s\",\"sequence\":%u}",
                     sent_at, seq);
    assert(n > 0 && (size_t)n < sizeof unsigned_buf);
    char hex[9];
    meter_crc32_hex((const unsigned char *)unsigned_buf, (size_t)n, hex);
    int m = snprintf(out, cap,
                     "{\"integrity\":{\"algorithm\":\"crc32\",\"value\":\"%s\"},"
                     "\"payload\":{\"global_resets\":[],\"usage\":[]},"
                     "\"protocol\":\"cdm/1\",\"sent_at\":\"%s\",\"sequence\":%u}\n",
                     hex, sent_at, seq);
    assert(m > 0 && (size_t)m < cap);
    return (size_t)m;
}

int main(void) {
    meter_receiver_t r;
    meter_receiver_init(&r);
    char f[4096];

    /* Accept 7 at t=1000. */
    size_t l7 = build_frame(f, sizeof f, 7, "2026-09-10T00:04:59Z");
    CHECK(meter_receiver_accept(&r, (const unsigned char *)f, l7, 1000, NULL) ==
          METER_FRAME_OK);
    CHECK(r.has_seq && r.seq == 7 && r.has_payload);
    CHECK(r.stale == 0);

    /* Receive-age stale boundary: 299 fresh, 300 stale. */
    meter_receiver_update_stale(&r, 1000 + 299);
    CHECK(r.stale == 0);
    meter_receiver_update_stale(&r, 1000 + 300);
    CHECK(r.stale == 1);

    /* Duplicate 7 rejected; last-good kept. */
    size_t l7b = build_frame(f, sizeof f, 7, "2026-09-10T00:05:00Z");
    CHECK(meter_receiver_accept(&r, (const unsigned char *)f, l7b, 1400, NULL) !=
          METER_FRAME_OK);
    CHECK(r.seq == 7 && r.has_payload);
    CHECK(strcmp(r.sent_at, "2026-09-10T00:04:59Z") == 0);

    /* Reverse 6 rejected. */
    size_t l6 = build_frame(f, sizeof f, 6, "2026-09-10T00:05:01Z");
    CHECK(meter_receiver_accept(&r, (const unsigned char *)f, l6, 1401, NULL) !=
          METER_FRAME_OK);
    CHECK(r.seq == 7);

    /* Half-range jump rejected (7 -> 7+2^31). */
    {
        char fh[4096];
        size_t lh = build_frame(fh, sizeof fh, 7 + 0x80000000u, "2026-09-10T00:05:02Z");
        CHECK(meter_receiver_accept(&r, (const unsigned char *)fh, lh, 1402, NULL) !=
              METER_FRAME_OK);
        CHECK(r.seq == 7);
    }

    /* New sent_at alone never resets the sequence. */
    size_t l8 = build_frame(f, sizeof f, 8, "2026-09-10T00:06:00Z");
    CHECK(meter_receiver_accept(&r, (const unsigned char *)f, l8, 1500, NULL) ==
          METER_FRAME_OK);
    CHECK(r.seq == 8);
    CHECK(r.stale == 0); /* fresh frame clears receive-age staleness */

    /* Stale/disconnect does not reset the sequence: aged to stale, then a
     * duplicate of 8 is still rejected and 9 accepted. */
    meter_receiver_update_stale(&r, 1500 + 5000);
    CHECK(r.stale == 1);
    size_t l8b = build_frame(f, sizeof f, 8, "2026-09-10T00:07:00Z");
    CHECK(meter_receiver_accept(&r, (const unsigned char *)f, l8b, 7000, NULL) !=
          METER_FRAME_OK);
    size_t l9 = build_frame(f, sizeof f, 9, "2026-09-10T00:07:01Z");
    CHECK(meter_receiver_accept(&r, (const unsigned char *)f, l9, 7001, NULL) ==
          METER_FRAME_OK);
    CHECK(r.seq == 9);

    /* Wrap: 4294967295 -> 0 accepted. */
    {
        meter_receiver_t w;
        meter_receiver_init(&w);
        char fw[4096];
        size_t lw = build_frame(fw, sizeof fw, 4294967295u, "2026-09-10T00:04:59Z");
        CHECK(meter_receiver_accept(&w, (const unsigned char *)fw, lw, 10, NULL) ==
              METER_FRAME_OK);
        size_t l0 = build_frame(fw, sizeof fw, 0, "2026-09-10T00:05:00Z");
        CHECK(meter_receiver_accept(&w, (const unsigned char *)fw, l0, 11, NULL) ==
              METER_FRAME_OK);
        CHECK(w.seq == 0);
    }

    /* Corrupt line keeps last-good and records the error. */
    {
        const char bad[] = "{\"protocol\":\"cdm/1\"}\n";
        CHECK(meter_receiver_accept(&r, (const unsigned char *)bad, sizeof bad - 1,
                                    8000, NULL) != METER_FRAME_OK);
        CHECK(r.seq == 9 && r.has_payload);
        CHECK(r.last_error[0] != '\0');
    }

    /* Explicit reset is the only path that clears the sequence. */
    meter_receiver_reset(&r);
    CHECK(!r.has_seq && !r.has_payload);
    size_t l1 = build_frame(f, sizeof f, 1, "2026-09-10T00:08:00Z");
    CHECK(meter_receiver_accept(&r, (const unsigned char *)f, l1, 9000, NULL) ==
          METER_FRAME_OK);

    if (failures == 0) {
        printf("test_meter_state: PASS\n");
        return 0;
    }
    printf("test_meter_state: %d FAILURES\n", failures);
    return 1;
}
