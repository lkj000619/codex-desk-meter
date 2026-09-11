#ifndef METER_PARSER_H
#define METER_PARSER_H

#include "meter_model.h"
#include <cJSON.h>
#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

bool meter_parse_rfc3339(const char *str, int64_t *out_epoch_sec);
bool meter_is_valid_rfc3339(const char *str);

/* Parse usage JSON payload into inout_snap.
 * If error_str is non-empty, sets error_code and preserves last known good data.
 * If json payload is invalid or fields are missing/out-of-range, sets error_code and preserves last data.
 * If valid, updates snapshot and clears error_code.
 */
int meter_parse_usage_json(const char *json_str, const char *now_str, const char *error_str, usage_snapshot_t *inout_snap);

/* Parse global reset JSON payload into inout_snap.
 * Supports codex-reset.com and codex-resets.com.
 */
int meter_parse_global_reset_json(const char *json_str, const char *expected_provider, const char *now_str, const char *error_str, global_reset_snapshot_t *inout_snap);

/* Serialization helpers returning newly allocated cJSON object (caller frees with cJSON_Delete) */
cJSON *meter_serialize_usage_to_cjson(const usage_snapshot_t *snap);
cJSON *meter_serialize_global_reset_to_cjson(const global_reset_snapshot_t *snap);

#ifdef __cplusplus
}
#endif

#endif /* METER_PARSER_H */
