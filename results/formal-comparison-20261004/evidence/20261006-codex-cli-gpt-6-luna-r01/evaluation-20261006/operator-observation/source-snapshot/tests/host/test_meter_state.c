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
    meter_receiver_t receiver;
    meter_receiver_init(&receiver);
    char frame[512];
    size_t length = make_frame(7, frame, sizeof(frame));
    assert(meter_receiver_receive(&receiver, (const uint8_t *)frame, length, 0));
    meter_receiver_poll(&receiver, 299999);
    assert(!receiver.receive_stale);
    meter_receiver_poll(&receiver, 300000);
    assert(receiver.receive_stale);

    length = make_frame(1, frame, sizeof(frame));
    assert(!meter_receiver_receive(&receiver, (const uint8_t *)frame, length, 300001));
    assert(strcmp(receiver.last_error, "OUT_OF_ORDER_SEQUENCE") == 0);
    assert(receiver.sequence == 7 && receiver.receive_stale);

    length = make_frame(8, frame, sizeof(frame));
    assert(meter_receiver_receive(&receiver, (const uint8_t *)frame, length, 301000));
    assert(receiver.sequence == 8 && !receiver.receive_stale && receiver.last_error[0] == '\0');

    meter_receiver_deinit(&receiver);
    return 0;
}
