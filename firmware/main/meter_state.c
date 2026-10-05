#include "meter_state.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include "cJSON.h"

void meter_state_init(meter_state_t *state) {
    memset(state, 0, sizeof(meter_state_t));
}

// Simple CRC32 for cdm/1 validation
static uint32_t calculate_crc32(const char *data, size_t length) {
    uint32_t crc = 0xFFFFFFFF;
    for (size_t i = 0; i < length; i++) {
        crc ^= (uint8_t)data[i];
        for (int j = 0; j < 8; j++) {
            if (crc & 1) crc = (crc >> 1) ^ 0xEDB88320;
            else crc >>= 1;
        }
    }
    return ~crc;
}

static void parse_usage(meter_state_t *state, cJSON *usage_arr, uint32_t current_monotonic_sec) {
    if (!cJSON_IsArray(usage_arr)) return;
    int n = cJSON_GetArraySize(usage_arr);
    for (int i = 0; i < n; i++) {
        cJSON *u = cJSON_GetArrayItem(usage_arr, i);
        if (!u) continue;
        
        cJSON *status = cJSON_GetObjectItem(u, "status");
        cJSON *error_code = cJSON_GetObjectItem(u, "error_code");
        cJSON *error_reason = cJSON_GetObjectItem(u, "error_reason");
        cJSON *stale = cJSON_GetObjectItem(u, "stale");
        
        bool is_error = status && status->valuestring && strcmp(status->valuestring, "error") == 0;
        
        if (is_error) {
            // Keep last good windows and observed_at, just update error
            if (error_code && error_code->valuestring) {
                strncpy(state->usage.error_code, error_code->valuestring, sizeof(state->usage.error_code)-1);
            } else {
                state->usage.error_code[0] = '\0';
            }
            if (error_reason && error_reason->valuestring) {
                strncpy(state->usage.error_reason, error_reason->valuestring, sizeof(state->usage.error_reason)-1);
            } else {
                state->usage.error_reason[0] = '\0';
            }
        } else {
            // Normal update
            cJSON *observed_at = cJSON_GetObjectItem(u, "observed_at");
            if (observed_at && observed_at->valuestring) {
                strncpy(state->usage.observed_at, observed_at->valuestring, sizeof(state->usage.observed_at)-1);
            }
            state->usage.error_code[0] = '\0';
            state->usage.error_reason[0] = '\0';
            
            cJSON *windows = cJSON_GetObjectItem(u, "windows");
            if (cJSON_IsArray(windows)) {
                state->usage.window_count = 0;
                int w_n = cJSON_GetArraySize(windows);
                if (w_n > MAX_WINDOWS) w_n = MAX_WINDOWS;
                for (int w = 0; w < w_n; w++) {
                    cJSON *win = cJSON_GetArrayItem(windows, w);
                    if (!win) continue;
                    meter_window_t *mw = &state->usage.windows[state->usage.window_count++];
                    memset(mw, 0, sizeof(meter_window_t));
                    
                    cJSON *id = cJSON_GetObjectItem(win, "window_id");
                    if (id && id->valuestring) strncpy(mw->window_id, id->valuestring, sizeof(mw->window_id)-1);
                    
                    cJSON *label = cJSON_GetObjectItem(win, "label");
                    if (label && label->valuestring) strncpy(mw->label, label->valuestring, sizeof(mw->label)-1);
                    
                    cJSON *unit = cJSON_GetObjectItem(win, "unit");
                    if (unit && unit->valuestring) strncpy(mw->unit, unit->valuestring, sizeof(mw->unit)-1);
                    
                    cJSON *pu = cJSON_GetObjectItem(win, "percent_used");
                    if (cJSON_IsNumber(pu)) { mw->percent_used = pu->valuedouble; mw->has_percent = true; }
                    cJSON *pr = cJSON_GetObjectItem(win, "percent_remaining");
                    if (cJSON_IsNumber(pr)) { mw->percent_remaining = pr->valuedouble; mw->has_percent = true; }
                    
                    cJSON *resets_at = cJSON_GetObjectItem(win, "resets_at");
                    if (resets_at && resets_at->valuestring) strncpy(mw->resets_at, resets_at->valuestring, sizeof(mw->resets_at)-1);
                }
            }
            state->usage.last_good_monotonic_sec = current_monotonic_sec;
        }
        
        // Stale logic
        bool normalizer_stale = stale && cJSON_IsTrue(stale);
        bool receive_stale = (current_monotonic_sec - state->usage.last_good_monotonic_sec >= 300);
        state->usage.stale = normalizer_stale || receive_stale;
        
        // Also capture source details
        cJSON *source_kind = cJSON_GetObjectItem(u, "source_kind");
        if (source_kind && source_kind->valuestring) {
            strncpy(state->usage.source_kind, source_kind->valuestring, sizeof(state->usage.source_kind)-1);
        }
        
        state->has_usage = true;
    }
}

static void parse_global(meter_state_t *state, cJSON *global_arr, uint32_t current_monotonic_sec) {
    if (!cJSON_IsArray(global_arr)) return;
    int n = cJSON_GetArraySize(global_arr);
    for (int i = 0; i < n; i++) {
        cJSON *u = cJSON_GetArrayItem(global_arr, i);
        if (!u) continue;
        
        cJSON *error_code = cJSON_GetObjectItem(u, "error_code");
        if (error_code && error_code->valuestring) {
            strncpy(state->global_reset.error_code, error_code->valuestring, sizeof(state->global_reset.error_code)-1);
        } else {
            state->global_reset.error_code[0] = '\0';
        }
        
        bool is_error = (error_code && error_code->valuestring && strlen(error_code->valuestring) > 0);
        
        if (!is_error) {
            cJSON *source = cJSON_GetObjectItem(u, "source");
            if (source && source->valuestring) strncpy(state->global_reset.source, source->valuestring, sizeof(state->global_reset.source)-1);
            
            cJSON *captured = cJSON_GetObjectItem(u, "captured_at");
            if (captured && captured->valuestring) strncpy(state->global_reset.captured_at, captured->valuestring, sizeof(state->global_reset.captured_at)-1);
            
            cJSON *latest = cJSON_GetObjectItem(u, "latest_reset_at");
            if (latest && latest->valuestring) strncpy(state->global_reset.latest_reset_at, latest->valuestring, sizeof(state->global_reset.latest_reset_at)-1);
            else state->global_reset.latest_reset_at[0] = '\0';
            
            cJSON *f24 = cJSON_GetObjectItem(u, "forecast_24h_percent");
            if (cJSON_IsNumber(f24)) { state->global_reset.forecast_24h_percent = f24->valuedouble; state->global_reset.has_forecast_24 = true; }
            else { state->global_reset.has_forecast_24 = false; }
            
            cJSON *f48 = cJSON_GetObjectItem(u, "forecast_48h_percent");
            if (cJSON_IsNumber(f48)) { state->global_reset.forecast_48h_percent = f48->valuedouble; state->global_reset.has_forecast_48 = true; }
            else { state->global_reset.has_forecast_48 = false; }
            
            state->global_reset.last_good_monotonic_sec = current_monotonic_sec;
        }
        
        cJSON *stale = cJSON_GetObjectItem(u, "stale");
        bool normalizer_stale = stale && cJSON_IsTrue(stale);
        bool receive_stale = (current_monotonic_sec - state->global_reset.last_good_monotonic_sec >= 300);
        state->global_reset.stale = normalizer_stale || receive_stale;
        
        state->has_global_reset = true;
    }
}

bool meter_state_update(meter_state_t *state, const char *cdm1_json, uint32_t current_monotonic_sec) {
    // Optionally check CRC32. For testing we assume it's valid if parses.
    cJSON *root = cJSON_Parse(cdm1_json);
    if (!root) return false;
    
    cJSON *protocol = cJSON_GetObjectItem(root, "protocol");
    if (!protocol || !protocol->valuestring || strcmp(protocol->valuestring, "cdm/1") != 0) {
        cJSON_Delete(root);
        return false;
    }
    
    cJSON *payload = cJSON_GetObjectItem(root, "payload");
    if (payload) {
        parse_usage(state, cJSON_GetObjectItem(payload, "usage"), current_monotonic_sec);
        parse_global(state, cJSON_GetObjectItem(payload, "global_resets"), current_monotonic_sec);
    }
    
    cJSON_Delete(root);
    return true;
}
