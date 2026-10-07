#include "meter_parser.h"
#include "meter_crc.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

static void test_rfc3339(void)
{
    int64_t sec = 0;
    assert(meter_parse_rfc3339("2026-09-10T00:00:00Z", &sec));
    assert(sec > 0);

    /* Test roundtrip format */
    char buf[32];
    meter_format_rfc3339(sec, buf, sizeof(buf));
    assert(strcmp(buf, "2026-09-10T00:00:00Z") == 0);

    /* Test offsets */
    int64_t sec_offset = 0;
    assert(meter_parse_rfc3339("2026-09-10T09:00:00+09:00", &sec_offset));
    assert(sec == sec_offset);

    /* Test invalid dates */
    assert(!meter_parse_rfc3339("invalid-date", &sec));
    assert(!meter_parse_rfc3339("2026-02-30T00:00:00Z", &sec));
    assert(!meter_parse_rfc3339("2026-09-10T25:00:00Z", &sec));
    assert(!meter_parse_rfc3339("2026-09-10T00:00:00", &sec)); /* missing timezone */

    printf("test_rfc3339 passed\n");
}

static void test_sequence_logic(void)
{
    /* Normal increment */
    assert(meter_sequence_is_newer(1, 0));
    assert(meter_sequence_is_newer(2, 1));
    assert(meter_sequence_is_newer(100, 99));

    /* Duplicate rejected */
    assert(!meter_sequence_is_newer(5, 5));

    /* Backwards rejected */
    assert(!meter_sequence_is_newer(4, 5));

    /* Wrap-around: 0 is newer than 4294967295 */
    assert(meter_sequence_is_newer(0, 4294967295u));
    assert(meter_sequence_is_newer(1, 4294967295u));

    /* Half-range limit (2^31) */
    assert(!meter_sequence_is_newer(2147483648u, 0));
    assert(meter_sequence_is_newer(2147483647u, 0));

    printf("test_sequence_logic passed\n");
}

static void test_crc_and_canonical_frame(void)
{
    /* Example canonical frame:
     * {"integrity":{"algorithm":"crc32","value":"BE8028D7"},"payload":{"global_resets":[],"usage":[]},"protocol":"cdm/1","sent_at":"2026-09-10T00:00:00Z","sequence":1}\n
     */
    const char *valid_line =
        "{\"integrity\":{\"algorithm\":\"crc32\",\"value\":\"BE8028D7\"},\"payload\":{\"global_resets\":[],\"usage\":[]},\"protocol\":\"cdm/1\",\"sent_at\":\"2026-09-10T00:00:00Z\",\"sequence\":1}\n";

    char exp_crc[9] = {0}, act_crc[9] = {0};
    assert(meter_verify_frame_crc(valid_line, strlen(valid_line), exp_crc, act_crc));
    assert(strcmp(act_crc, "BE8028D7") == 0);

    /* Corrupted CRC */
    const char *bad_crc_line =
        "{\"integrity\":{\"algorithm\":\"crc32\",\"value\":\"FFFFFFFF\"},\"payload\":{\"global_resets\":[],\"usage\":[]},\"protocol\":\"cdm/1\",\"sent_at\":\"2026-09-10T00:00:00Z\",\"sequence\":1}\n";
    assert(!meter_verify_frame_crc(bad_crc_line, strlen(bad_crc_line), exp_crc, act_crc));

    /* Missing newline */
    const char *no_nl =
        "{\"integrity\":{\"algorithm\":\"crc32\",\"value\":\"BE8028D7\"},\"payload\":{\"global_resets\":[],\"usage\":[]},\"protocol\":\"cdm/1\",\"sent_at\":\"2026-09-10T00:00:00Z\",\"sequence\":1}";
    assert(!meter_verify_frame_crc(no_nl, strlen(no_nl), exp_crc, act_crc));

    /* Embedded CRLF */
    const char *crlf_line =
        "{\"integrity\":{\"algorithm\":\"crc32\",\"value\":\"BE8028D7\"},\"payload\":{\"global_resets\":[],\"usage\":[]},\"protocol\":\"cdm/1\",\"sent_at\":\"2026-09-10T00:00:00Z\",\"sequence\":1}\r\n";
    assert(!meter_verify_frame_crc(crlf_line, strlen(crlf_line), exp_crc, act_crc));

    /* Full frame parse */
    meter_frame_t frame;
    char err[32] = {0};
    assert(meter_parse_frame(valid_line, strlen(valid_line), &frame, err));
    assert(frame.sequence == 1);
    assert(strcmp(frame.protocol, "cdm/1") == 0);
    assert(strcmp(frame.sent_at, "2026-09-10T00:00:00Z") == 0);
    assert(frame.usage_count == 0);

    printf("test_crc_and_canonical_frame passed\n");
}

int main(void)
{
    test_rfc3339();
    test_sequence_logic();
    test_crc_and_canonical_frame();
    printf("ALL METER_PARSER TESTS PASSED!\n");
    return 0;
}
