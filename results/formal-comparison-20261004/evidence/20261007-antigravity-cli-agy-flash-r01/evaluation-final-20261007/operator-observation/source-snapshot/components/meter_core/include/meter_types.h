#ifndef METER_TYPES_H
#define METER_TYPES_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

#define METER_PROTOCOL "cdm/1"
#define METER_MAX_FRAME_BYTES (64 * 1024)
#define METER_STALE_THRESHOLD_SECONDS 300
#define METER_MAX_WINDOWS_PER_SNAPSHOT 8
#define METER_MAX_SNAPSHOTS 16
#define METER_MAX_GLOBAL_RESETS 8
#define METER_MAX_STRING_LEN 64
#define METER_MAX_REASON_LEN 128

typedef enum {
    UNIT_UNKNOWN = 0,
    UNIT_PERCENT,
    UNIT_TOKEN,
    UNIT_CREDIT
} meter_unit_t;

typedef enum {
    SNAPSHOT_STATUS_UNKNOWN = 0,
    SNAPSHOT_STATUS_AVAILABLE,
    SNAPSHOT_STATUS_UNAVAILABLE,
    SNAPSHOT_STATUS_UNSUPPORTED,
    SNAPSHOT_STATUS_UNAUTHORIZED,
    SNAPSHOT_STATUS_ERROR,
    SNAPSHOT_STATUS_STALE
} snapshot_status_t;

typedef enum {
    RESET_STATUS_UNKNOWN = 0,
    RESET_STATUS_SCHEDULED,
    RESET_STATUS_EXPIRED
} reset_status_t;

typedef struct {
    char window_id[METER_MAX_STRING_LEN];
    char label[METER_MAX_STRING_LEN];
    meter_unit_t unit;
    double used_units;
    double remaining_units;
    double limit_units;
    bool has_absolute;
    double percent_used;
    double percent_remaining;
    bool has_percent;
    char resets_at[METER_MAX_STRING_LEN];
    reset_status_t reset_status;
} meter_window_t;

typedef struct {
    char snapshot_id[METER_MAX_STRING_LEN];
    char provider_id[METER_MAX_STRING_LEN];
    char agent_id[METER_MAX_STRING_LEN];
    char host_id[METER_MAX_STRING_LEN];
    char model_id[METER_MAX_STRING_LEN];
    char account_profile_id[METER_MAX_STRING_LEN];
    char source_kind[METER_MAX_STRING_LEN];
    char metric_kind[METER_MAX_STRING_LEN];
    meter_unit_t unit;
    snapshot_status_t status;
    char observed_at[METER_MAX_STRING_LEN];
    char last_good_at[METER_MAX_STRING_LEN];
    bool stale;
    char error_code[METER_MAX_STRING_LEN];
    char error_reason[METER_MAX_REASON_LEN];
    meter_window_t windows[METER_MAX_WINDOWS_PER_SNAPSHOT];
    size_t window_count;
} meter_snapshot_t;

typedef struct {
    int schema_version;
    char source[METER_MAX_STRING_LEN];
    char captured_at[METER_MAX_STRING_LEN];
    char latest_reset_at[METER_MAX_STRING_LEN];
    double forecast_24h_percent;
    bool has_forecast_24h;
    double forecast_48h_percent;
    bool has_forecast_48h;
    bool forecast_is_schedule;
    bool stale;
    char error_code[METER_MAX_STRING_LEN];
} meter_global_reset_t;

typedef struct {
    char protocol[16];
    uint32_t sequence;
    char sent_at[METER_MAX_STRING_LEN];
    char integrity_algo[16];
    char integrity_value[16];
    meter_snapshot_t usage[METER_MAX_SNAPSHOTS];
    size_t usage_count;
    meter_global_reset_t global_resets[METER_MAX_GLOBAL_RESETS];
    size_t global_reset_count;
} meter_frame_t;

typedef enum {
    SCREEN_DASHBOARD = 0,
    SCREEN_GLOBAL_RESETS,
    SCREEN_STATUS_ERROR,
    SCREEN_MAX_COUNT
} screen_mode_t;

typedef enum {
    ORIENTATION_LANDSCAPE_NORMAL = 0,  /* 0 deg landscape (820x320) */
    ORIENTATION_LANDSCAPE_INVERTED = 1 /* 180 deg landscape (820x320) */
} display_orientation_t;

#ifdef __cplusplus
}
#endif

#endif /* METER_TYPES_H */
