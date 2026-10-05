#ifndef METER_STATE_H
#define METER_STATE_H

#include <stdint.h>
#include <stdbool.h>

#define MAX_WINDOWS 10

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    char window_id[64];
    char label[64];
    double used_units;
    double remaining_units;
    double limit_units;
    char unit[16];
    double percent_used;
    double percent_remaining;
    char resets_at[32];
    char reset_status[16];
    bool has_absolute;
    bool has_percent;
} meter_window_t;

typedef struct {
    char source_kind[32];
    char provider_id[64];
    char agent_id[64];
    char host_id[64];
    char model_id[64];
    char account_profile_id[64];
    char metric_kind[32];
    char unit[16];
    char status[32];
    char observed_at[32];
    char last_good_at[32];
    char error_code[64];
    char error_reason[128];
    bool stale;
    meter_window_t windows[MAX_WINDOWS];
    int window_count;
    
    uint32_t last_good_monotonic_sec;
} meter_usage_state_t;

typedef struct {
    char source[64];
    char captured_at[32];
    char latest_reset_at[32];
    double forecast_24h_percent;
    double forecast_48h_percent;
    bool forecast_is_schedule;
    bool stale;
    char error_code[64];
    
    bool has_forecast_24;
    bool has_forecast_48;
    
    uint32_t last_good_monotonic_sec;
} meter_global_reset_t;

typedef struct {
    meter_usage_state_t usage;
    meter_global_reset_t global_reset;
    bool has_usage;
    bool has_global_reset;
} meter_state_t;

void meter_state_init(meter_state_t *state);
bool meter_state_update(meter_state_t *state, const char *cdm1_json, uint32_t current_monotonic_sec);

#ifdef __cplusplus
}
#endif

#endif // METER_STATE_H
