#include "meter_core.h"

#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>

static void report_result(const meter_receiver_t *receiver, bool accepted)
{
    printf("{\"accepted\":%s,\"has_sequence\":%s,\"has_good_frame\":%s,"
           "\"sequence\":%" PRIu32 ",\"receive_stale\":%s,"
           "\"last_error\":\"%s\",\"last_good_length\":%zu}\n",
           accepted ? "true" : "false",
           receiver->has_sequence ? "true" : "false",
           receiver->has_good_frame ? "true" : "false",
           receiver->sequence,
           receiver->receive_stale ? "true" : "false",
           receiver->last_error,
           receiver->last_good_length);
    fflush(stdout);
}

int main(void)
{
    uint8_t *line = (uint8_t *)malloc(METER_MAX_FRAME_BYTES + 1u);
    if (!line) return 2;

    meter_receiver_t receiver;
    meter_receiver_init(&receiver);
    size_t length = 0;
    bool overflow = false;
    uint64_t monotonic_ms = 0;
    int input;
    while ((input = getchar()) != EOF) {
        if (!overflow) {
            if (length < METER_MAX_FRAME_BYTES + 1u) line[length++] = (uint8_t)input;
            else overflow = true;
        }
        if (input == '\n') {
            size_t supplied = overflow ? METER_MAX_FRAME_BYTES + 1u : length;
            bool accepted = meter_receiver_receive(&receiver, line, supplied, monotonic_ms);
            report_result(&receiver, accepted);
            monotonic_ms++;
            length = 0;
            overflow = false;
        }
    }
    if (ferror(stdin)) {
        meter_receiver_deinit(&receiver);
        free(line);
        return 3;
    }
    if (length || overflow) {
        size_t supplied = overflow ? METER_MAX_FRAME_BYTES + 1u : length;
        bool accepted = meter_receiver_receive(&receiver, line, supplied, monotonic_ms);
        report_result(&receiver, accepted);
    }
    meter_receiver_deinit(&receiver);
    free(line);
    return 0;
}
