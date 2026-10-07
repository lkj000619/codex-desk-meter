#ifndef METER_CRC_H
#define METER_CRC_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

uint32_t meter_crc32(const uint8_t *data, size_t length);
void meter_crc32_hex(uint32_t crc, char out_hex[9]);

#ifdef __cplusplus
}
#endif

#endif /* METER_CRC_H */
