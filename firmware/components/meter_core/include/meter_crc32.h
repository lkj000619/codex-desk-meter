#pragma once
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* CRC32 (IEEE, polynomial 0xEDB88320), init 0xFFFFFFFF, xorout 0xFFFFFFFF.
 * Matches Python zlib.crc32() so host and firmware agree on cdm/1 integrity. */
uint32_t meter_crc32(const uint8_t *data, size_t len);

/* Format as 8 uppercase hex chars plus NUL. out must hold >= 9 bytes. */
void meter_crc32_hex(const uint8_t *data, size_t len, char out[9]);

#ifdef __cplusplus
}
#endif
