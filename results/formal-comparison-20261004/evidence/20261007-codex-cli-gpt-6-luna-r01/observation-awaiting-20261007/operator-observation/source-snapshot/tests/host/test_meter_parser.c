#include "meter_core.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static size_t make_frame(uint32_t sequence, char *output, size_t capacity)
{
    char unsigned_json[256];
    int n = snprintf(unsigned_json, sizeof(unsigned_json),
        "{\"payload\":{\"global_resets\":[],\"usage\":[]},\"protocol\":\"cdm/1\",\"sent_at\":\"2026-09-10T00:00:00Z\",\"sequence\":%u}",
        sequence);
    assert(n > 0 && (size_t)n < sizeof(unsigned_json));
    uint32_t crc = meter_crc32((const uint8_t *)unsigned_json, (size_t)n);
    n = snprintf(output, capacity,
        "{\"integrity\":{\"algorithm\":\"crc32\",\"value\":\"%08X\"},\"payload\":{\"global_resets\":[],\"usage\":[]},\"protocol\":\"cdm/1\",\"sent_at\":\"2026-09-10T00:00:00Z\",\"sequence\":%u}\n",
        crc, sequence);
    assert(n > 0 && (size_t)n < capacity);
    return (size_t)n;
}

int main(void)
{
    char frame[512];
    size_t length = make_frame(7, frame, sizeof(frame));
    meter_receiver_t receiver;
    meter_receiver_init(&receiver);
    assert(meter_receiver_receive(&receiver, (const uint8_t *)frame, length, 10));
    assert(receiver.has_good_frame && receiver.sequence == 7 && receiver.last_error[0] == '\0');

    char corrupt[512];
    memcpy(corrupt, frame, length);
    corrupt[length - 3] ^= 1;
    assert(!meter_receiver_receive(&receiver, (const uint8_t *)corrupt, length, 20));
    assert(strcmp(receiver.last_error, "CRC_MISMATCH") == 0);
    assert(receiver.sequence == 7 && receiver.last_good_length == length);
    assert(memcmp(receiver.last_good_line, frame, length) == 0);

    char crlf[514];
    memcpy(crlf, frame, length - 1);
    crlf[length - 1] = '\r'; crlf[length] = '\n';
    assert(!meter_receiver_receive(&receiver, (const uint8_t *)crlf, length + 1, 30));
    assert(strcmp(receiver.last_error, "FRAME_NEWLINE_INVALID") == 0);

    char pretty[512];
    int pretty_len = snprintf(pretty, sizeof(pretty), "{ \"integrity\": {\"algorithm\":\"crc32\",\"value\":\"00000000\"} }\n");
    assert(!meter_receiver_receive(&receiver, (const uint8_t *)pretty, (size_t)pretty_len, 40));

    assert(meter_sequence_is_newer(0, UINT32_MAX));
    assert(!meter_sequence_is_newer(UINT32_MAX, 0));
    assert(!meter_sequence_is_newer(7, 7));
    assert(!meter_sequence_is_newer(0x80000007u, 7));

    int64_t delta = -1;
    assert(meter_timestamp_delta_seconds("2026-09-10T00:04:59Z", "2026-09-10T00:00:00Z", &delta));
    assert(delta == 299);
    assert(!meter_source_is_stale("2026-09-10T00:04:59Z", "2026-09-10T00:00:00Z", 0));
    assert(meter_source_is_stale("2026-09-10T00:04:59Z", "2026-09-10T00:00:00Z", 1000));
    meter_receiver_deinit(&receiver);
    return 0;
}
