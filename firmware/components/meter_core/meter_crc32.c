#include "meter_crc32.h"

static uint32_t s_table[256];
static int s_ready = 0;

static void ensure_table(void) {
    if (s_ready) {
        return;
    }
    for (uint32_t i = 0; i < 256; i++) {
        uint32_t c = i;
        for (int k = 0; k < 8; k++) {
            c = (c & 1) ? (0xEDB88320u ^ (c >> 1)) : (c >> 1);
        }
        s_table[i] = c;
    }
    s_ready = 1;
}

uint32_t meter_crc32(const uint8_t *data, size_t len) {
    ensure_table();
    uint32_t crc = 0xFFFFFFFFu;
    for (size_t i = 0; i < len; i++) {
        crc = s_table[(crc ^ data[i]) & 0xFF] ^ (crc >> 8);
    }
    return crc ^ 0xFFFFFFFFu;
}

void meter_crc32_hex(const uint8_t *data, size_t len, char out[9]) {
    static const char *hex = "0123456789ABCDEF";
    uint32_t crc = meter_crc32(data, len);
    for (int i = 7; i >= 0; i--) {
        out[i] = hex[crc & 0xF];
        crc >>= 4;
    }
    out[8] = '\0';
}
