#include "meter_parser.h"
#include "meter_state.h"
#include <cJSON.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(void)
{
    /* Read all stdin into memory */
    size_t cap = 64 * 1024;
    size_t len = 0;
    char *buf = (char *)malloc(cap);
    if (!buf) return 1;

    while (1) {
        size_t n = fread(buf + len, 1, cap - len - 1, stdin);
        if (n == 0) break;
        len += n;
        if (len + 1024 >= cap) {
            cap *= 2;
            buf = (char *)realloc(buf, cap);
            if (!buf) return 1;
        }
    }
    buf[len] = '\0';

    meter_legacy_request_t req;
    if (!meter_parse_legacy_request(buf, &req)) {
        fprintf(stderr, "Failed to parse legacy request JSON\n");
        free(buf);
        return 1;
    }
    free(buf);

    cJSON *out_array = cJSON_CreateArray();

    /* State across events in this run */
    bool is_fixture = (strcmp(req.source, "fixture") == 0);

    /* Last-good tracking */
    cJSON *lg_windows = NULL;
    char lg_observed_at[64] = {0};
    int64_t lg_obs_sec = 0;

    char lg_fetched_at[64] = {0};
    int64_t lg_fetched_sec = 0;
    char lg_latest_reset_at[64] = {0};
    double lg_f24 = 0.0;
    bool has_lg_f24 = false;
    double lg_f48 = 0.0;
    bool has_lg_f48 = false;

    for (size_t i = 0; i < req.event_count; ++i) {
        meter_legacy_event_t *ev = &req.events[i];
        int64_t now_sec = ev->now_seconds;

        const char *err_code = NULL;

        if (ev->error[0] != '\0') {
            err_code = ev->error;
        } else if (!ev->body_raw || ev->body_raw[0] == '\0') {
            err_code = "EMPTY_BODY";
        } else {
            /* Try parsing body JSON */
            cJSON *body = cJSON_Parse(ev->body_raw);
            if (!body) {
                err_code = "MALFORMED_JSON";
            } else {
                cJSON *cj_cap = cJSON_GetObjectItemCaseSensitive(body, "captured_at");
                if (!cj_cap || !cJSON_IsString(cj_cap) || !cj_cap->valuestring) {
                    err_code = "MISSING_CAPTURED_AT";
                } else {
                    int64_t cap_sec = 0;
                    if (!meter_parse_rfc3339(cj_cap->valuestring, &cap_sec)) {
                        err_code = "TIMESTAMP_INVALID";
                    } else if (now_sec > 0 && cap_sec > now_sec) {
                        err_code = "FUTURE_TIMESTAMP";
                    } else if (is_fixture) {
                        /* Validate fixture windows */
                        cJSON *windows = cJSON_GetObjectItemCaseSensitive(body, "windows");
                        if (!windows || !cJSON_IsArray(windows)) {
                            err_code = "MISSING_WINDOWS";
                        } else {
                            /* Check window percentages */
                            cJSON *w = NULL;
                            bool win_invalid = false;
                            cJSON_ArrayForEach(w, windows) {
                                cJSON *pu = cJSON_GetObjectItemCaseSensitive(w, "percent_used");
                                if (pu && cJSON_IsNumber(pu)) {
                                    if (pu->valuedouble < 0.0 || pu->valuedouble > 100.0) {
                                        win_invalid = true;
                                        break;
                                    }
                                }
                            }
                            if (win_invalid) {
                                err_code = "PERCENTAGE_INVALID";
                            } else {
                                /* Update last-good */
                                if (lg_windows) cJSON_Delete(lg_windows);
                                lg_windows = cJSON_Duplicate(windows, 1);
                                strncpy(lg_observed_at, cj_cap->valuestring, sizeof(lg_observed_at)-1);
                                lg_obs_sec = cap_sec;
                            }
                        }
                    } else {
                        /* Global reset source */
                        cJSON *f24 = cJSON_GetObjectItemCaseSensitive(body, "forecast_24h_percent");
                        if (f24 && cJSON_IsNumber(f24) && f24->valuedouble < 0.0) {
                            err_code = "FORECAST_INVALID";
                        } else {
                            strncpy(lg_fetched_at, cj_cap->valuestring, sizeof(lg_fetched_at)-1);
                            lg_fetched_sec = cap_sec;

                            cJSON *l_rst = cJSON_GetObjectItemCaseSensitive(body, "last_reset_at");
                            if (!l_rst) l_rst = cJSON_GetObjectItemCaseSensitive(body, "latest_reset_at");
                            if (l_rst && cJSON_IsString(l_rst)) {
                                strncpy(lg_latest_reset_at, l_rst->valuestring, sizeof(lg_latest_reset_at)-1);
                            }

                            if (f24 && cJSON_IsNumber(f24)) {
                                lg_f24 = f24->valuedouble;
                                has_lg_f24 = true;
                            } else {
                                has_lg_f24 = false;
                            }

                            cJSON *f48 = cJSON_GetObjectItemCaseSensitive(body, "forecast_48h_percent");
                            if (f48 && cJSON_IsNumber(f48)) {
                                lg_f48 = f48->valuedouble;
                                has_lg_f48 = true;
                            } else {
                                has_lg_f48 = false;
                            }
                        }
                    }
                }
                cJSON_Delete(body);
            }
        }

        /* Build snapshot output for event */
        cJSON *out_snap = cJSON_CreateObject();
        if (is_fixture) {
            cJSON_AddStringToObject(out_snap, "source", "fixture");
            if (lg_windows) {
                cJSON_AddItemToObject(out_snap, "windows", cJSON_Duplicate(lg_windows, 1));
            } else {
                cJSON_AddArrayToObject(out_snap, "windows");
            }
            cJSON_AddStringToObject(out_snap, "observed_at", lg_observed_at);
            bool stale = (lg_obs_sec > 0 && (now_sec - lg_obs_sec >= METER_STALE_THRESHOLD_SECONDS));
            cJSON_AddBoolToObject(out_snap, "stale", stale);
            if (err_code) {
                cJSON_AddStringToObject(out_snap, "error_code", err_code);
            } else {
                cJSON_AddNullToObject(out_snap, "error_code");
            }
        } else {
            cJSON_AddStringToObject(out_snap, "provider", req.source);
            cJSON_AddStringToObject(out_snap, "fetched_at", lg_fetched_at);
            if (lg_latest_reset_at[0] != '\0') {
                cJSON_AddStringToObject(out_snap, "latest_reset_at", lg_latest_reset_at);
            } else {
                cJSON_AddNullToObject(out_snap, "latest_reset_at");
            }

            if (has_lg_f24) {
                cJSON_AddNumberToObject(out_snap, "forecast_24h_percent", lg_f24);
            } else {
                cJSON_AddNullToObject(out_snap, "forecast_24h_percent");
            }

            if (has_lg_f48) {
                cJSON_AddNumberToObject(out_snap, "forecast_48h_percent", lg_f48);
            } else {
                cJSON_AddNullToObject(out_snap, "forecast_48h_percent");
            }

            cJSON_AddBoolToObject(out_snap, "forecast_is_schedule", false);
            bool stale = (lg_fetched_sec > 0 && (now_sec - lg_fetched_sec >= METER_STALE_THRESHOLD_SECONDS));
            cJSON_AddBoolToObject(out_snap, "stale", stale);
            if (err_code) {
                cJSON_AddStringToObject(out_snap, "error_code", err_code);
            } else {
                cJSON_AddNullToObject(out_snap, "error_code");
            }
        }

        cJSON_AddItemToArray(out_array, out_snap);
    }

    if (lg_windows) cJSON_Delete(lg_windows);
    meter_free_legacy_request(&req);

    char *out_json = cJSON_PrintUnformatted(out_array);
    cJSON_Delete(out_array);

    if (out_json) {
        printf("%s\n", out_json);
        free(out_json);
    }

    fprintf(stderr, "[meter_legacy_adapter] Processed %u events\n", (unsigned int)req.event_count);
    return 0;
}
