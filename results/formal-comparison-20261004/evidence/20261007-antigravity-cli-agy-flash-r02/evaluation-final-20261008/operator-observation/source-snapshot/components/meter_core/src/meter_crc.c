#include "meter_crc.h"
#include <stdio.h>

static uint32_t s_crc_table[256];
static int s_table_initialized = 0;

static void init_crc_table(void)
{
    uint32_t poly = 0xEDB88320u;
    for (uint32_t i = 0; i < 256; ++i) {
        uint32_t c = i;
        for (int j = 0; j < 8; ++j) {
            c = (c & 1) ? (poly ^ (c >> 1)) : (c >> 1);
        }
        s_crc_table[i] = c;
    }
    s_table_initialized = 1;
}

uint32_t meter_crc32(const uint8_t *data, size_t length)
{
    if (!s_table_initialized) {
        init_crc_table();
    }
    uint32_t c = 0xFFFFFFFFu;
    for (size_t i = 0; i < length; ++i) {
        c = s_crc_table[(c ^ data[i]) & 0xFF] ^ (c >> 8);
    }
    return c ^ 0xFFFFFFFFu;
}

void meter_crc32_hex(uint32_t crc, char out_hex[9])
{
    snprintf(out_hex, 9, "%08X", (unsigned int)crc);
}
