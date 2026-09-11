#ifndef METER_MODEL_H
#define METER_MODEL_H

#include <stdbool.h>
#include <stdint.h>

#define METER_MAX_WINDOWS 8
#define METER_STR_LEN_SHORT 32
#define METER_STR_LEN_MED 64
#define METER_STR_LEN_LONG 128

typedef struct {
    char id[METER_STR_LEN_SHORT];
    char label[METER_STR_LEN_MED];
    bool has_percent_used;
    int32_t percent_used;         /* 0..100 */
    bool has_percent_remaining;
    int32_t percent_remaining;    /* 0..100 */
    bool has_resets_at;
    char resets_at[METER_STR_LEN_MED]; /* RFC3339 or null */
} usage_window_t;

typedef struct {
    char source[METER_STR_LEN_SHORT]; /* "fixture" | "live" | "unknown" */
    bool has_observed_at;
    char observed_at[METER_STR_LEN_MED]; /* RFC3339 or null */
    int window_count;
    usage_window_t windows[METER_MAX_WINDOWS];
    bool stale;
    bool has_error_code;
    char error_code[METER_STR_LEN_MED]; /* null when has_error_code == false */
} usage_snapshot_t;

typedef struct {
    char provider[METER_STR_LEN_MED]; /* "codex-reset.com" | "codex-resets.com" */
    bool has_latest_reset_at;
    char latest_reset_at[METER_STR_LEN_MED]; /* RFC3339 or null */
    bool has_fetched_at;
    char fetched_at[METER_STR_LEN_MED]; /* RFC3339 or null */
    bool has_forecast_24h;
    int32_t forecast_24h_percent; /* 0..100 */
    bool has_forecast_48h;
    int32_t forecast_48h_percent; /* 0..100 */
    bool forecast_is_schedule;    /* always false */
    bool stale;
    bool has_error_code;
    char error_code[METER_STR_LEN_MED]; /* null when has_error_code == false */
} global_reset_snapshot_t;

typedef struct {
    usage_snapshot_t usage;
    global_reset_snapshot_t reset_forecast; /* codex-reset.com */
    global_reset_snapshot_t reset_history;  /* codex-resets.com */
    uint32_t current_screen; /* 0: Dashboard, 1: Global Reset, 2: Status/Error */
    uint32_t last_success_update_sec;
    bool wifi_connected;
    char last_error_msg[METER_STR_LEN_LONG];
} meter_state_t;

#endif /* METER_MODEL_H */
