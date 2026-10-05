#include <iostream>
#include <string>
#include <vector>
#include <sstream>
#include <ctime>
#include <iomanip>
#include <cstring>
#include "cJSON.h"
#include "meter_state.h"

// Parse ISO8601 subset like 2026-09-10T00:04:59Z
static uint32_t parse_time(const char *iso) {
    if (!iso) return 0;
    struct tm t;
    memset(&t, 0, sizeof(t));
    sscanf(iso, "%d-%d-%dT%d:%d:%dZ", &t.tm_year, &t.tm_mon, &t.tm_mday, &t.tm_hour, &t.tm_min, &t.tm_sec);
    t.tm_year -= 1900;
    t.tm_mon -= 1;
    // We don't need real timezone handling if we just want relative seconds
    // Fake it using mktime, ignoring timezone because we only do subtraction
    time_t res = mktime(&t);
    return (uint32_t)res;
}

int main() {
    std::string input_str;
    std::string line;
    while (std::getline(std::cin, line)) {
        input_str += line + "\n";
    }

    cJSON *input_json = cJSON_Parse(input_str.c_str());
    if (!input_json) {
        std::cerr << "Invalid JSON input" << std::endl;
        return 1;
    }

    cJSON *source_obj = cJSON_GetObjectItem(input_json, "source");
    cJSON *events = cJSON_GetObjectItem(input_json, "events");

    if (!source_obj || !events || !cJSON_IsArray(events)) {
        std::cerr << "Missing source or events" << std::endl;
        return 1;
    }
    
    std::string test_source = source_obj->valuestring;

    meter_state_t state;
    meter_state_init(&state);

    cJSON *output_snapshots = cJSON_CreateArray();

    uint32_t base_time = 0;
    bool base_time_set = false;

    int num_events = cJSON_GetArraySize(events);
    for (int i = 0; i < num_events; i++) {
        cJSON *event = cJSON_GetArrayItem(events, i);
        cJSON *now_obj = cJSON_GetObjectItem(event, "now");
        cJSON *body_obj = cJSON_GetObjectItem(event, "body");
        cJSON *error_obj = cJSON_GetObjectItem(event, "error");

        uint32_t now_sec = 0;
        if (now_obj && now_obj->valuestring) {
            now_sec = parse_time(now_obj->valuestring);
            if (!base_time_set) {
                base_time = now_sec;
                base_time_set = true;
            }
        }
        
        uint32_t monotonic_sec = now_sec - base_time;

        // Mock the normalizer building cdm/1
        cJSON *cdm1 = cJSON_CreateObject();
        cJSON_AddStringToObject(cdm1, "protocol", "cdm/1");
        cJSON_AddNumberToObject(cdm1, "sequence", i + 1);
        if (now_obj && now_obj->valuestring) {
            cJSON_AddStringToObject(cdm1, "sent_at", now_obj->valuestring);
        }
        cJSON *payload = cJSON_CreateObject();
        cJSON_AddItemToObject(cdm1, "payload", payload);

        if (test_source == "fixture") {
            cJSON *usage_arr = cJSON_CreateArray();
            cJSON_AddItemToObject(payload, "usage", usage_arr);
            cJSON *u = cJSON_CreateObject();
            cJSON_AddItemToArray(usage_arr, u);
            cJSON_AddStringToObject(u, "source_kind", "fixture");
            
            if (error_obj && !cJSON_IsNull(error_obj)) {
                cJSON_AddStringToObject(u, "status", "error");
                cJSON_AddStringToObject(u, "error_code", error_obj->valuestring);
                cJSON_AddStringToObject(u, "error_reason", "mocked error");
            } else if (body_obj && !cJSON_IsNull(body_obj) && cJSON_IsObject(body_obj)) {
                cJSON_AddStringToObject(u, "status", "available");
                cJSON *cap = cJSON_GetObjectItem(body_obj, "captured_at");
                if (cap && cap->valuestring) {
                    cJSON_AddStringToObject(u, "observed_at", cap->valuestring);
                    uint32_t cap_sec = parse_time(cap->valuestring);
                    bool stale = (now_sec - cap_sec >= 300);
                    cJSON_AddBoolToObject(u, "stale", stale);
                }
                cJSON *win = cJSON_GetObjectItem(body_obj, "windows");
                if (win) {
                    cJSON_AddItemReferenceToObject(u, "windows", win);
                }
            } else {
                cJSON_AddStringToObject(u, "status", "error");
                cJSON_AddStringToObject(u, "error_code", "parse_error");
            }
        } else {
            cJSON *glob_arr = cJSON_CreateArray();
            cJSON_AddItemToObject(payload, "global_resets", glob_arr);
            cJSON *g = cJSON_CreateObject();
            cJSON_AddItemToArray(glob_arr, g);
            cJSON_AddStringToObject(g, "source", test_source.c_str());
            
            if (error_obj && !cJSON_IsNull(error_obj)) {
                cJSON_AddStringToObject(g, "error_code", error_obj->valuestring);
            } else if (body_obj && !cJSON_IsNull(body_obj) && cJSON_IsObject(body_obj)) {
                cJSON *cap = cJSON_GetObjectItem(body_obj, "captured_at");
                if (cap && cap->valuestring) {
                    cJSON_AddStringToObject(g, "captured_at", cap->valuestring);
                    uint32_t cap_sec = parse_time(cap->valuestring);
                    bool stale = (now_sec - cap_sec >= 300);
                    cJSON_AddBoolToObject(g, "stale", stale);
                }
                cJSON *last_reset = cJSON_GetObjectItem(body_obj, "last_reset_at");
                if (!last_reset) last_reset = cJSON_GetObjectItem(body_obj, "latest_reset_at");
                if (last_reset && last_reset->valuestring) {
                    cJSON_AddStringToObject(g, "latest_reset_at", last_reset->valuestring);
                }
                cJSON *f24 = cJSON_GetObjectItem(body_obj, "forecast_24h_percent");
                if (f24 && cJSON_IsNumber(f24)) {
                    cJSON_AddNumberToObject(g, "forecast_24h_percent", f24->valuedouble);
                }
                cJSON *f48 = cJSON_GetObjectItem(body_obj, "forecast_48h_percent");
                if (f48 && cJSON_IsNumber(f48)) {
                    cJSON_AddNumberToObject(g, "forecast_48h_percent", f48->valuedouble);
                }
            } else {
                cJSON_AddStringToObject(g, "error_code", "parse_error");
            }
        }

        char *cdm1_str = cJSON_PrintUnformatted(cdm1);
        meter_state_update(&state, cdm1_str, monotonic_sec);
        free(cdm1_str);
        cJSON_Delete(cdm1);

        // Generate snapshot for this event
        cJSON *snap = cJSON_CreateObject();
        if (test_source == "fixture") {
            cJSON_AddStringToObject(snap, "source", "fixture");
            if (strlen(state.usage.observed_at) > 0) {
                cJSON_AddStringToObject(snap, "observed_at", state.usage.observed_at);
            } else {
                cJSON_AddNullToObject(snap, "observed_at");
            }
            cJSON_AddBoolToObject(snap, "stale", state.usage.stale);
            if (strlen(state.usage.error_code) > 0) {
                cJSON_AddStringToObject(snap, "error_code", state.usage.error_code);
            } else {
                cJSON_AddNullToObject(snap, "error_code");
            }
            
            cJSON *win_arr = cJSON_CreateArray();
            for (int w = 0; w < state.usage.window_count; w++) {
                cJSON *wo = cJSON_CreateObject();
                cJSON_AddStringToObject(wo, "id", state.usage.windows[w].window_id);
                if (state.usage.windows[w].has_percent) {
                    cJSON_AddNumberToObject(wo, "percent_used", state.usage.windows[w].percent_used);
                    cJSON_AddNumberToObject(wo, "percent_remaining", state.usage.windows[w].percent_remaining);
                }
                cJSON_AddItemToArray(win_arr, wo);
            }
            cJSON_AddItemToObject(snap, "windows", win_arr);
        } else {
            cJSON_AddStringToObject(snap, "provider", state.global_reset.source);
            if (strlen(state.global_reset.captured_at) > 0) {
                cJSON_AddStringToObject(snap, "fetched_at", state.global_reset.captured_at);
            } else {
                cJSON_AddNullToObject(snap, "fetched_at");
            }
            if (strlen(state.global_reset.latest_reset_at) > 0) {
                cJSON_AddStringToObject(snap, "latest_reset_at", state.global_reset.latest_reset_at);
            } else {
                cJSON_AddNullToObject(snap, "latest_reset_at");
            }
            if (state.global_reset.has_forecast_24) {
                cJSON_AddNumberToObject(snap, "forecast_24h_percent", state.global_reset.forecast_24h_percent);
            } else {
                cJSON_AddNullToObject(snap, "forecast_24h_percent");
            }
            if (state.global_reset.has_forecast_48) {
                cJSON_AddNumberToObject(snap, "forecast_48h_percent", state.global_reset.forecast_48h_percent);
            } else {
                cJSON_AddNullToObject(snap, "forecast_48h_percent");
            }
            cJSON_AddBoolToObject(snap, "forecast_is_schedule", false);
            cJSON_AddBoolToObject(snap, "stale", state.global_reset.stale);
            if (strlen(state.global_reset.error_code) > 0) {
                cJSON_AddStringToObject(snap, "error_code", state.global_reset.error_code);
            } else {
                cJSON_AddNullToObject(snap, "error_code");
            }
        }
        
        cJSON_AddItemToArray(output_snapshots, snap);
    }

    char *out_str = cJSON_PrintUnformatted(output_snapshots);
    std::cout << out_str << std::endl;
    free(out_str);

    cJSON_Delete(output_snapshots);
    cJSON_Delete(input_json);
    return 0;
}
