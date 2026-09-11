#include "meter_parser.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static bool is_leap_year(int y) {
    return (y % 4 == 0 && (y % 100 != 0 || y % 400 == 0));
}

static const int days_in_month[12] = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};

bool meter_parse_rfc3339(const char *str, int64_t *out_epoch_sec) {
    if (!str || strlen(str) < 20) return false;
    int year, month, day, hour, min, sec;
    char tz = 0;
    int tz_hr = 0, tz_min = 0;
    int n = sscanf(str, "%4d-%2d-%2dT%2d:%2d:%2d%c", &year, &month, &day, &hour, &min, &sec, &tz);
    if (n < 6) return false;
    if (year < 1970 || year > 2100 || month < 1 || month > 12 || day < 1 || hour < 0 || hour > 23 || min < 0 || min > 59 || sec < 0 || sec > 60) {
        return false;
    }
    int max_day = days_in_month[month - 1];
    if (month == 2 && is_leap_year(year)) max_day = 29;
    if (day > max_day) return false;

    int tz_offset_sec = 0;
    if (tz == '+' || tz == '-') {
        const char *p = strchr(str, tz);
        if (p && sscanf(p, "%c%2d:%2d", &tz, &tz_hr, &tz_min) >= 3) {
            tz_offset_sec = (tz_hr * 3600 + tz_min * 60) * (tz == '-' ? -1 : 1);
        }
    }

    int64_t days = 0;
    for (int y = 1970; y < year; y++) {
        days += is_leap_year(y) ? 366 : 365;
    }
    for (int m = 1; m < month; m++) {
        days += days_in_month[m - 1];
        if (m == 2 && is_leap_year(year)) days += 1;
    }
    days += (day - 1);

    int64_t total_sec = days * 86400LL + hour * 3600LL + min * 60LL + sec - tz_offset_sec;
    if (out_epoch_sec) *out_epoch_sec = total_sec;
    return true;
}

bool meter_is_valid_rfc3339(const char *str) {
    return meter_parse_rfc3339(str, NULL);
}

int meter_parse_usage_json(const char *json_str, const char *now_str, const char *error_str, usage_snapshot_t *inout_snap) {
    if (!inout_snap) return -1;

    int64_t now_sec = 0;
    bool has_now = meter_parse_rfc3339(now_str, &now_sec);

    if (error_str && strlen(error_str) > 0) {
        inout_snap->has_error_code = true;
        strncpy(inout_snap->error_code, error_str, sizeof(inout_snap->error_code) - 1);
        inout_snap->error_code[sizeof(inout_snap->error_code) - 1] = 0;
        return 0;
    }

    if (!json_str || strlen(json_str) == 0) {
        inout_snap->has_error_code = true;
        strncpy(inout_snap->error_code, "empty_payload", sizeof(inout_snap->error_code) - 1);
        inout_snap->error_code[sizeof(inout_snap->error_code) - 1] = 0;
        return -1;
    }

    cJSON *root = cJSON_Parse(json_str);
    if (!root) {
        inout_snap->has_error_code = true;
        strncpy(inout_snap->error_code, "parse_error", sizeof(inout_snap->error_code) - 1);
        inout_snap->error_code[sizeof(inout_snap->error_code) - 1] = 0;
        return -1;
    }

    cJSON *src = cJSON_GetObjectItem(root, "source");
    cJSON *cap = cJSON_GetObjectItem(root, "captured_at");
    cJSON *win_arr = cJSON_GetObjectItem(root, "windows");

    if (!src || !cJSON_IsString(src) || !cap || !cJSON_IsString(cap) || !win_arr || !cJSON_IsArray(win_arr)) {
        cJSON_Delete(root);
        inout_snap->has_error_code = true;
        strncpy(inout_snap->error_code, "missing_fields", sizeof(inout_snap->error_code) - 1);
        inout_snap->error_code[sizeof(inout_snap->error_code) - 1] = 0;
        return -1;
    }

    int64_t cap_sec = 0;
    if (!meter_parse_rfc3339(cap->valuestring, &cap_sec)) {
        cJSON_Delete(root);
        inout_snap->has_error_code = true;
        strncpy(inout_snap->error_code, "invalid_date", sizeof(inout_snap->error_code) - 1);
        inout_snap->error_code[sizeof(inout_snap->error_code) - 1] = 0;
        return -1;
    }

    if (has_now && (now_sec < cap_sec)) {
        cJSON_Delete(root);
        inout_snap->has_error_code = true;
        strncpy(inout_snap->error_code, "future_date", sizeof(inout_snap->error_code) - 1);
        inout_snap->error_code[sizeof(inout_snap->error_code) - 1] = 0;
        return -1;
    }

    usage_snapshot_t temp;
    memset(&temp, 0, sizeof(temp));
    strncpy(temp.source, src->valuestring, sizeof(temp.source) - 1);
    temp.has_observed_at = true;
    strncpy(temp.observed_at, cap->valuestring, sizeof(temp.observed_at) - 1);

    int count = cJSON_GetArraySize(win_arr);
    if (count > METER_MAX_WINDOWS) count = METER_MAX_WINDOWS;
    temp.window_count = count;

    for (int i = 0; i < count; i++) {
        cJSON *item = cJSON_GetArrayItem(win_arr, i);
        if (!item || !cJSON_IsObject(item)) {
            cJSON_Delete(root);
            inout_snap->has_error_code = true;
            strncpy(inout_snap->error_code, "invalid_window", sizeof(inout_snap->error_code) - 1);
            inout_snap->error_code[sizeof(inout_snap->error_code) - 1] = 0;
            return -1;
        }
        cJSON *jid = cJSON_GetObjectItem(item, "id");
        cJSON *jlbl = cJSON_GetObjectItem(item, "label");
        cJSON *ju = cJSON_GetObjectItem(item, "percent_used");
        cJSON *jr = cJSON_GetObjectItem(item, "percent_remaining");
        cJSON *jres = cJSON_GetObjectItem(item, "resets_at");

        if (jid && cJSON_IsString(jid)) strncpy(temp.windows[i].id, jid->valuestring, sizeof(temp.windows[i].id) - 1);
        if (jlbl && cJSON_IsString(jlbl)) strncpy(temp.windows[i].label, jlbl->valuestring, sizeof(temp.windows[i].label) - 1);

        if (ju && cJSON_IsNumber(ju)) {
            if (ju->valueint < 0 || ju->valueint > 100) {
                cJSON_Delete(root);
                inout_snap->has_error_code = true;
                strncpy(inout_snap->error_code, "out_of_range", sizeof(inout_snap->error_code) - 1);
                inout_snap->error_code[sizeof(inout_snap->error_code) - 1] = 0;
                return -1;
            }
            temp.windows[i].has_percent_used = true;
            temp.windows[i].percent_used = (int32_t)ju->valueint;
        } else {
            temp.windows[i].has_percent_used = false;
        }

        if (jr && cJSON_IsNumber(jr)) {
            if (jr->valueint < 0 || jr->valueint > 100) {
                cJSON_Delete(root);
                inout_snap->has_error_code = true;
                strncpy(inout_snap->error_code, "out_of_range", sizeof(inout_snap->error_code) - 1);
                inout_snap->error_code[sizeof(inout_snap->error_code) - 1] = 0;
                return -1;
            }
            temp.windows[i].has_percent_remaining = true;
            temp.windows[i].percent_remaining = (int32_t)jr->valueint;
        } else {
            temp.windows[i].has_percent_remaining = false;
        }

        if (jres && cJSON_IsString(jres)) {
            temp.windows[i].has_resets_at = true;
            strncpy(temp.windows[i].resets_at, jres->valuestring, sizeof(temp.windows[i].resets_at) - 1);
        } else {
            temp.windows[i].has_resets_at = false;
        }
    }

    if (has_now) {
        temp.stale = ((now_sec - cap_sec) >= 300);
    } else {
        cJSON *jstale = cJSON_GetObjectItem(root, "stale");
        temp.stale = (jstale && cJSON_IsTrue(jstale));
    }

    cJSON_Delete(root);

    temp.has_error_code = false;
    temp.error_code[0] = 0;
    memcpy(inout_snap, &temp, sizeof(usage_snapshot_t));
    return 0;
}

int meter_parse_global_reset_json(const char *json_str, const char *expected_provider, const char *now_str, const char *error_str, global_reset_snapshot_t *inout_snap) {
    if (!inout_snap) return -1;

    int64_t now_sec = 0;
    bool has_now = meter_parse_rfc3339(now_str, &now_sec);

    if (error_str && strlen(error_str) > 0) {
        inout_snap->has_error_code = true;
        strncpy(inout_snap->error_code, error_str, sizeof(inout_snap->error_code) - 1);
        inout_snap->error_code[sizeof(inout_snap->error_code) - 1] = 0;
        return 0;
    }

    if (!json_str || strlen(json_str) == 0) {
        inout_snap->has_error_code = true;
        strncpy(inout_snap->error_code, "empty_payload", sizeof(inout_snap->error_code) - 1);
        inout_snap->error_code[sizeof(inout_snap->error_code) - 1] = 0;
        return -1;
    }

    cJSON *root = cJSON_Parse(json_str);
    if (!root) {
        inout_snap->has_error_code = true;
        strncpy(inout_snap->error_code, "parse_error", sizeof(inout_snap->error_code) - 1);
        inout_snap->error_code[sizeof(inout_snap->error_code) - 1] = 0;
        return -1;
    }

    cJSON *src = cJSON_GetObjectItem(root, "source");
    cJSON *cap = cJSON_GetObjectItem(root, "captured_at");

    if (!src || !cJSON_IsString(src) || !cap || !cJSON_IsString(cap)) {
        cJSON_Delete(root);
        inout_snap->has_error_code = true;
        strncpy(inout_snap->error_code, "missing_fields", sizeof(inout_snap->error_code) - 1);
        inout_snap->error_code[sizeof(inout_snap->error_code) - 1] = 0;
        return -1;
    }

    int64_t cap_sec = 0;
    if (!meter_parse_rfc3339(cap->valuestring, &cap_sec)) {
        cJSON_Delete(root);
        inout_snap->has_error_code = true;
        strncpy(inout_snap->error_code, "invalid_date", sizeof(inout_snap->error_code) - 1);
        inout_snap->error_code[sizeof(inout_snap->error_code) - 1] = 0;
        return -1;
    }

    if (has_now && (now_sec < cap_sec)) {
        cJSON_Delete(root);
        inout_snap->has_error_code = true;
        strncpy(inout_snap->error_code, "future_date", sizeof(inout_snap->error_code) - 1);
        inout_snap->error_code[sizeof(inout_snap->error_code) - 1] = 0;
        return -1;
    }

    global_reset_snapshot_t temp;
    memset(&temp, 0, sizeof(temp));
    strncpy(temp.provider, src->valuestring, sizeof(temp.provider) - 1);
    temp.has_fetched_at = true;
    strncpy(temp.fetched_at, cap->valuestring, sizeof(temp.fetched_at) - 1);

    cJSON *lreset = cJSON_GetObjectItem(root, "last_reset_at");
    if (!lreset) lreset = cJSON_GetObjectItem(root, "latest_reset_at");
    if (lreset && cJSON_IsString(lreset)) {
        int64_t lr_sec = 0;
        if (!meter_parse_rfc3339(lreset->valuestring, &lr_sec)) {
            cJSON_Delete(root);
            inout_snap->has_error_code = true;
            strncpy(inout_snap->error_code, "invalid_latest_reset", sizeof(inout_snap->error_code) - 1);
            inout_snap->error_code[sizeof(inout_snap->error_code) - 1] = 0;
            return -1;
        }
        if (has_now && (now_sec < lr_sec)) {
            cJSON_Delete(root);
            inout_snap->has_error_code = true;
            strncpy(inout_snap->error_code, "future_latest_reset", sizeof(inout_snap->error_code) - 1);
            inout_snap->error_code[sizeof(inout_snap->error_code) - 1] = 0;
            return -1;
        }
        temp.has_latest_reset_at = true;
        strncpy(temp.latest_reset_at, lreset->valuestring, sizeof(temp.latest_reset_at) - 1);
    } else {
        temp.has_latest_reset_at = false;
    }

    cJSON *f24 = cJSON_GetObjectItem(root, "forecast_24h_percent");
    if (f24 && cJSON_IsNumber(f24)) {
        if (f24->valueint < 0 || f24->valueint > 100) {
            cJSON_Delete(root);
            inout_snap->has_error_code = true;
            strncpy(inout_snap->error_code, "out_of_range", sizeof(inout_snap->error_code) - 1);
            inout_snap->error_code[sizeof(inout_snap->error_code) - 1] = 0;
            return -1;
        }
        temp.has_forecast_24h = true;
        temp.forecast_24h_percent = (int32_t)f24->valueint;
    } else {
        temp.has_forecast_24h = false;
    }

    cJSON *f48 = cJSON_GetObjectItem(root, "forecast_48h_percent");
    if (f48 && cJSON_IsNumber(f48)) {
        if (f48->valueint < 0 || f48->valueint > 100) {
            cJSON_Delete(root);
            inout_snap->has_error_code = true;
            strncpy(inout_snap->error_code, "out_of_range", sizeof(inout_snap->error_code) - 1);
            inout_snap->error_code[sizeof(inout_snap->error_code) - 1] = 0;
            return -1;
        }
        temp.has_forecast_48h = true;
        temp.forecast_48h_percent = (int32_t)f48->valueint;
    } else {
        temp.has_forecast_48h = false;
    }

    temp.forecast_is_schedule = false;

    if (has_now) {
        temp.stale = ((now_sec - cap_sec) >= 300);
    } else {
        cJSON *jstale = cJSON_GetObjectItem(root, "stale");
        temp.stale = (jstale && cJSON_IsTrue(jstale));
    }

    cJSON_Delete(root);

    temp.has_error_code = false;
    temp.error_code[0] = 0;
    memcpy(inout_snap, &temp, sizeof(global_reset_snapshot_t));
    return 0;
}

cJSON *meter_serialize_usage_to_cjson(const usage_snapshot_t *snap) {
    if (!snap) return NULL;
    cJSON *root = cJSON_CreateObject();
    cJSON_AddStringToObject(root, "source", snap->source[0] ? snap->source : "unknown");
    if (snap->has_observed_at) {
        cJSON_AddStringToObject(root, "observed_at", snap->observed_at);
    } else {
        cJSON_AddNullToObject(root, "observed_at");
    }

    cJSON *win_arr = cJSON_CreateArray();
    for (int i = 0; i < snap->window_count; i++) {
        cJSON *item = cJSON_CreateObject();
        cJSON_AddStringToObject(item, "id", snap->windows[i].id);
        cJSON_AddStringToObject(item, "label", snap->windows[i].label);
        if (snap->windows[i].has_percent_used) {
            cJSON_AddNumberToObject(item, "percent_used", snap->windows[i].percent_used);
        } else {
            cJSON_AddNullToObject(item, "percent_used");
        }
        if (snap->windows[i].has_percent_remaining) {
            cJSON_AddNumberToObject(item, "percent_remaining", snap->windows[i].percent_remaining);
        } else {
            cJSON_AddNullToObject(item, "percent_remaining");
        }
        if (snap->windows[i].has_resets_at) {
            cJSON_AddStringToObject(item, "resets_at", snap->windows[i].resets_at);
        } else {
            cJSON_AddNullToObject(item, "resets_at");
        }
        cJSON_AddItemToArray(win_arr, item);
    }
    cJSON_AddItemToObject(root, "windows", win_arr);
    cJSON_AddBoolToObject(root, "stale", snap->stale);

    if (snap->has_error_code && snap->error_code[0] != 0) {
        cJSON_AddStringToObject(root, "error_code", snap->error_code);
    } else {
        cJSON_AddNullToObject(root, "error_code");
    }
    return root;
}

cJSON *meter_serialize_global_reset_to_cjson(const global_reset_snapshot_t *snap) {
    if (!snap) return NULL;
    cJSON *root = cJSON_CreateObject();
    cJSON_AddStringToObject(root, "provider", snap->provider[0] ? snap->provider : "unknown");
    if (snap->has_latest_reset_at) {
        cJSON_AddStringToObject(root, "latest_reset_at", snap->latest_reset_at);
    } else {
        cJSON_AddNullToObject(root, "latest_reset_at");
    }
    if (snap->has_fetched_at) {
        cJSON_AddStringToObject(root, "fetched_at", snap->fetched_at);
    } else {
        cJSON_AddNullToObject(root, "fetched_at");
    }
    if (snap->has_forecast_24h) {
        cJSON_AddNumberToObject(root, "forecast_24h_percent", snap->forecast_24h_percent);
    } else {
        cJSON_AddNullToObject(root, "forecast_24h_percent");
    }
    if (snap->has_forecast_48h) {
        cJSON_AddNumberToObject(root, "forecast_48h_percent", snap->forecast_48h_percent);
    } else {
        cJSON_AddNullToObject(root, "forecast_48h_percent");
    }
    cJSON_AddBoolToObject(root, "forecast_is_schedule", false);
    cJSON_AddBoolToObject(root, "stale", snap->stale);

    if (snap->has_error_code && snap->error_code[0] != 0) {
        cJSON_AddStringToObject(root, "error_code", snap->error_code);
    } else {
        cJSON_AddNullToObject(root, "error_code");
    }
    return root;
}
