#include "meter_parser.h"
#include "meter_crc.h"
#include <cJSON.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <math.h>

static int is_leap_year(int year) {
    return (year % 4 == 0 && year % 100 != 0) || (year % 400 == 0);
}

static const int days_before_month[12] = {
    0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334
};

bool meter_parse_rfc3339(const char *str, int64_t *out_seconds)
{
    if (!str || !out_seconds) return false;
    int year, month, day, hour, min, sec;
    char tz[16] = {0};
    int n = sscanf(str, "%4d-%2d-%2dT%2d:%2d:%2d%15s", &year, &month, &day, &hour, &min, &sec, tz);
    if (n < 6) {
        return false;
    }
    if (year < 1970 || year > 2100 || month < 1 || month > 12 || day < 1 || day > 31 ||
        hour < 0 || hour > 23 || min < 0 || min > 59 || sec < 0 || sec > 60) {
        return false;
    }
    int dim = 31;
    if (month == 4 || month == 6 || month == 9 || month == 11) dim = 30;
    else if (month == 2) dim = is_leap_year(year) ? 29 : 28;
    if (day > dim) return false;

    int days = 0;
    for (int y = 1970; y < year; ++y) {
        days += is_leap_year(y) ? 366 : 365;
    }
    days += days_before_month[month - 1];
    if (month > 2 && is_leap_year(year)) {
        days += 1;
    }
    days += (day - 1);

    int64_t total_sec = ((int64_t)days * 86400LL) + (hour * 3600) + (min * 60) + sec;

    /* Timezone adjustment */
    if (tz[0] == 'Z' || tz[0] == 'z') {
        /* UTC, no offset */
    } else if (tz[0] == '+' || tz[0] == '-') {
        int thour = 0, tmin = 0;
        if (sscanf(tz + 1, "%2d:%2d", &thour, &tmin) == 2 || sscanf(tz + 1, "%2d%2d", &thour, &tmin) == 2) {
            int toff = thour * 3600 + tmin * 60;
            if (tz[0] == '+') total_sec -= toff;
            else total_sec += toff;
        } else {
            return false;
        }
    } else if (strlen(tz) == 0) {
        return false; /* Missing timezone */
    }

    *out_seconds = total_sec;
    return true;
}

void meter_format_rfc3339(int64_t seconds, char *out_str, size_t max_len)
{
    if (!out_str || max_len < 21) return;
    int64_t sec_in_day = seconds % 86400LL;
    int64_t total_days = seconds / 86400LL;
    if (sec_in_day < 0) {
        sec_in_day += 86400LL;
        total_days -= 1;
    }
    int hour = (int)(sec_in_day / 3600);
    int min = (int)((sec_in_day % 3600) / 60);
    int sec = (int)(sec_in_day % 60);

    int year = 1970;
    while (1) {
        int ydays = is_leap_year(year) ? 366 : 365;
        if (total_days >= ydays) {
            total_days -= ydays;
            year++;
        } else {
            break;
        }
    }
    int month = 1;
    for (int m = 1; m <= 12; ++m) {
        int mdays = 31;
        if (m == 4 || m == 6 || m == 9 || m == 11) mdays = 30;
        else if (m == 2) mdays = is_leap_year(year) ? 29 : 28;
        if (total_days >= mdays) {
            total_days -= mdays;
            month++;
        } else {
            break;
        }
    }
    int day = (int)total_days + 1;
    snprintf(out_str, max_len, "%04d-%02d-%02dT%02d:%02d:%02dZ", year, month, day, hour, min, sec);
}

bool meter_sequence_is_newer(uint32_t candidate, uint32_t current)
{
    uint32_t dist = candidate - current;
    return dist > 0 && dist < 0x80000000u;
}

bool meter_verify_frame_crc(const char *raw_line, size_t line_len, char out_expected_crc[9], char out_actual_crc[9])
{
    if (!raw_line || line_len < 50 || line_len > METER_MAX_FRAME_BYTES) {
        return false;
    }
    /* Line must end with newline */
    if (raw_line[line_len - 1] != '\n') {
        return false;
    }
    /* Check no embedded \r or extra \n */
    for (size_t i = 0; i < line_len - 1; ++i) {
        if (raw_line[i] == '\r' || raw_line[i] == '\n') return false;
    }

    const char *prefix = "{\"integrity\":{\"algorithm\":\"crc32\",\"value\":\"";
    size_t prefix_len = strlen(prefix);
    if (strncmp(raw_line, prefix, prefix_len) != 0) {
        return false;
    }
    char claimed_crc[9] = {0};
    memcpy(claimed_crc, raw_line + prefix_len, 8);
    for (int i = 0; i < 8; ++i) {
        if (!isxdigit((unsigned char)claimed_crc[i])) return false;
    }
    if (strncmp(raw_line + prefix_len + 8, "\"},", 3) != 0) {
        return false;
    }

    /* Build unsigned payload: '{' + (raw_line + prefix_len + 11) up to line_len - 1 */
    size_t rest_start = prefix_len + 11;
    size_t rest_len = (line_len - 1) - rest_start;
    size_t unsigned_len = 1 + rest_len;
    char *unsigned_buf = (char *)malloc(unsigned_len + 1);
    if (!unsigned_buf) return false;
    unsigned_buf[0] = '{';
    memcpy(unsigned_buf + 1, raw_line + rest_start, rest_len);
    unsigned_buf[unsigned_len] = '\0';

    uint32_t calc = meter_crc32((const uint8_t *)unsigned_buf, unsigned_len);
    free(unsigned_buf);

    char calc_hex[9] = {0};
    meter_crc32_hex(calc, calc_hex);

    if (out_expected_crc) strncpy(out_expected_crc, calc_hex, 9);
    if (out_actual_crc) strncpy(out_actual_crc, claimed_crc, 9);

    return (strcmp(calc_hex, claimed_crc) == 0);
}

static meter_unit_t parse_unit_str(const char *str) {
    if (!str) return UNIT_UNKNOWN;
    if (strcmp(str, "percent") == 0) return UNIT_PERCENT;
    if (strcmp(str, "token") == 0) return UNIT_TOKEN;
    if (strcmp(str, "credit") == 0) return UNIT_CREDIT;
    return UNIT_UNKNOWN;
}

static snapshot_status_t parse_status_str(const char *str) {
    if (!str) return SNAPSHOT_STATUS_UNKNOWN;
    if (strcmp(str, "available") == 0) return SNAPSHOT_STATUS_AVAILABLE;
    if (strcmp(str, "unavailable") == 0) return SNAPSHOT_STATUS_UNAVAILABLE;
    if (strcmp(str, "unsupported") == 0) return SNAPSHOT_STATUS_UNSUPPORTED;
    if (strcmp(str, "unauthorized") == 0) return SNAPSHOT_STATUS_UNAUTHORIZED;
    if (strcmp(str, "error") == 0) return SNAPSHOT_STATUS_ERROR;
    if (strcmp(str, "stale") == 0) return SNAPSHOT_STATUS_STALE;
    return SNAPSHOT_STATUS_UNKNOWN;
}

static bool parse_snapshot_obj(const cJSON *item, meter_snapshot_t *snap, char out_error[32])
{
    memset(snap, 0, sizeof(*snap));
    const cJSON *cj_id = cJSON_GetObjectItemCaseSensitive(item, "snapshot_id");
    const cJSON *cj_prov = cJSON_GetObjectItemCaseSensitive(item, "provider_id");
    const cJSON *cj_agent = cJSON_GetObjectItemCaseSensitive(item, "agent_id");
    const cJSON *cj_host = cJSON_GetObjectItemCaseSensitive(item, "host_id");
    const cJSON *cj_status = cJSON_GetObjectItemCaseSensitive(item, "status");
    const cJSON *cj_obs = cJSON_GetObjectItemCaseSensitive(item, "observed_at");
    const cJSON *cj_stale = cJSON_GetObjectItemCaseSensitive(item, "stale");
    const cJSON *cj_unit = cJSON_GetObjectItemCaseSensitive(item, "unit");

    if (!cJSON_IsString(cj_prov) || !cj_prov->valuestring) {
        strncpy(out_error, "IDENTITY_REQUIRED", 31);
        return false;
    }
    if (cj_id && cJSON_IsString(cj_id)) strncpy(snap->snapshot_id, cj_id->valuestring, sizeof(snap->snapshot_id)-1);
    strncpy(snap->provider_id, cj_prov->valuestring, sizeof(snap->provider_id)-1);
    if (cj_agent && cJSON_IsString(cj_agent)) strncpy(snap->agent_id, cj_agent->valuestring, sizeof(snap->agent_id)-1);
    if (cj_host && cJSON_IsString(cj_host)) strncpy(snap->host_id, cj_host->valuestring, sizeof(snap->host_id)-1);

    const cJSON *cj_model = cJSON_GetObjectItemCaseSensitive(item, "model_id");
    if (cj_model && cJSON_IsString(cj_model)) strncpy(snap->model_id, cj_model->valuestring, sizeof(snap->model_id)-1);

    const cJSON *cj_acct = cJSON_GetObjectItemCaseSensitive(item, "account_profile_id");
    if (cj_acct && cJSON_IsString(cj_acct)) strncpy(snap->account_profile_id, cj_acct->valuestring, sizeof(snap->account_profile_id)-1);

    if (cj_status && cJSON_IsString(cj_status)) snap->status = parse_status_str(cj_status->valuestring);
    if (cj_unit && cJSON_IsString(cj_unit)) snap->unit = parse_unit_str(cj_unit->valuestring);
    if (cj_stale && cJSON_IsBool(cj_stale)) snap->stale = cJSON_IsTrue(cj_stale);

    if (cj_obs && cJSON_IsString(cj_obs)) {
        strncpy(snap->observed_at, cj_obs->valuestring, sizeof(snap->observed_at)-1);
        int64_t obs_sec = 0;
        if (!meter_parse_rfc3339(snap->observed_at, &obs_sec)) {
            strncpy(out_error, "TIMESTAMP_INVALID", 31);
            return false;
        }
    }

    const cJSON *cj_lg = cJSON_GetObjectItemCaseSensitive(item, "last_good_at");
    if (cj_lg && cJSON_IsString(cj_lg)) strncpy(snap->last_good_at, cj_lg->valuestring, sizeof(snap->last_good_at)-1);

    const cJSON *cj_err = cJSON_GetObjectItemCaseSensitive(item, "error_code");
    if (cj_err && cJSON_IsString(cj_err)) strncpy(snap->error_code, cj_err->valuestring, sizeof(snap->error_code)-1);

    const cJSON *cj_reason = cJSON_GetObjectItemCaseSensitive(item, "error_reason");
    if (cj_reason && cJSON_IsString(cj_reason)) strncpy(snap->error_reason, cj_reason->valuestring, sizeof(snap->error_reason)-1);

    /* Windows */
    const cJSON *windows = cJSON_GetObjectItemCaseSensitive(item, "windows");
    if (windows && cJSON_IsArray(windows)) {
        const cJSON *w_item = NULL;
        cJSON_ArrayForEach(w_item, windows) {
            if (snap->window_count >= METER_MAX_WINDOWS_PER_SNAPSHOT) break;
            meter_window_t *w = &snap->windows[snap->window_count];
            memset(w, 0, sizeof(*w));

            const cJSON *wid = cJSON_GetObjectItemCaseSensitive(w_item, "window_id");
            if (wid && cJSON_IsString(wid)) strncpy(w->window_id, wid->valuestring, sizeof(w->window_id)-1);

            const cJSON *wunit = cJSON_GetObjectItemCaseSensitive(w_item, "unit");
            if (wunit && cJSON_IsString(wunit)) w->unit = parse_unit_str(wunit->valuestring);

            const cJSON *pu = cJSON_GetObjectItemCaseSensitive(w_item, "percent_used");
            const cJSON *pr = cJSON_GetObjectItemCaseSensitive(w_item, "percent_remaining");
            if (pu && cJSON_IsNumber(pu)) {
                w->percent_used = pu->valuedouble;
                if (w->percent_used < 0.0 || w->percent_used > 100.0) {
                    strncpy(out_error, "PERCENTAGE_INVALID", 31);
                    return false;
                }
                w->has_percent = true;
            }
            if (pr && cJSON_IsNumber(pr)) {
                w->percent_remaining = pr->valuedouble;
                w->has_percent = true;
            }
            if (pu && cJSON_IsNumber(pu) && pr && cJSON_IsNumber(pr)) {
                if (fabs((w->percent_used + w->percent_remaining) - 100.0) > 0.01) {
                    strncpy(out_error, "PERCENTAGE_INCONSISTENT", 31);
                    return false;
                }
            }

            const cJSON *uu = cJSON_GetObjectItemCaseSensitive(w_item, "used_units");
            const cJSON *ru = cJSON_GetObjectItemCaseSensitive(w_item, "remaining_units");
            const cJSON *lu = cJSON_GetObjectItemCaseSensitive(w_item, "limit_units");
            if (uu && cJSON_IsNumber(uu) && ru && cJSON_IsNumber(ru) && lu && cJSON_IsNumber(lu)) {
                w->used_units = uu->valuedouble;
                w->remaining_units = ru->valuedouble;
                w->limit_units = lu->valuedouble;
                w->has_absolute = true;
                if (fabs((w->used_units + w->remaining_units) - w->limit_units) > 0.01) {
                    strncpy(out_error, "ABSOLUTE_BALANCE_MISMATCH", 31);
                    return false;
                }
            }

            const cJSON *wreset = cJSON_GetObjectItemCaseSensitive(w_item, "resets_at");
            if (wreset && cJSON_IsString(wreset)) {
                strncpy(w->resets_at, wreset->valuestring, sizeof(w->resets_at)-1);
            }
            snap->window_count++;
        }
    }

    return true;
}

static bool parse_global_reset_obj(const cJSON *item, meter_global_reset_t *gr, char out_error[32])
{
    memset(gr, 0, sizeof(*gr));
    const cJSON *cjsrc = cJSON_GetObjectItemCaseSensitive(item, "source");
    if (!cjsrc) cjsrc = cJSON_GetObjectItemCaseSensitive(item, "provider");
    if (cjsrc && cJSON_IsString(cjsrc)) strncpy(gr->source, cjsrc->valuestring, sizeof(gr->source)-1);

    const cJSON *cjcap = cJSON_GetObjectItemCaseSensitive(item, "captured_at");
    if (!cjcap) cjcap = cJSON_GetObjectItemCaseSensitive(item, "fetched_at");
    if (cjcap && cJSON_IsString(cjcap)) {
        strncpy(gr->captured_at, cjcap->valuestring, sizeof(gr->captured_at)-1);
        int64_t cap_sec = 0;
        if (!meter_parse_rfc3339(gr->captured_at, &cap_sec)) {
            strncpy(out_error, "TIMESTAMP_INVALID", 31);
            return false;
        }
    }

    const cJSON *cjlat = cJSON_GetObjectItemCaseSensitive(item, "latest_reset_at");
    if (!cjlat) cjlat = cJSON_GetObjectItemCaseSensitive(item, "last_reset_at");
    if (cjlat && cJSON_IsString(cjlat)) strncpy(gr->latest_reset_at, cjlat->valuestring, sizeof(gr->latest_reset_at)-1);

    const cJSON *f24 = cJSON_GetObjectItemCaseSensitive(item, "forecast_24h_percent");
    if (f24 && cJSON_IsNumber(f24)) {
        gr->forecast_24h_percent = f24->valuedouble;
        if (gr->forecast_24h_percent < 0.0) {
            strncpy(out_error, "FORECAST_INVALID", 31);
            return false;
        }
        gr->has_forecast_24h = true;
    }
    const cJSON *f48 = cJSON_GetObjectItemCaseSensitive(item, "forecast_48h_percent");
    if (f48 && cJSON_IsNumber(f48)) {
        gr->forecast_48h_percent = f48->valuedouble;
        gr->has_forecast_48h = true;
    }

    const cJSON *cjst = cJSON_GetObjectItemCaseSensitive(item, "stale");
    if (cjst && cJSON_IsBool(cjst)) gr->stale = cJSON_IsTrue(cjst);

    const cJSON *cjerr = cJSON_GetObjectItemCaseSensitive(item, "error_code");
    if (cjerr && cJSON_IsString(cjerr)) strncpy(gr->error_code, cjerr->valuestring, sizeof(gr->error_code)-1);

    return true;
}

bool meter_parse_frame(const char *raw_line, size_t line_len, meter_frame_t *out_frame, char out_error_code[32])
{
    if (!raw_line || !out_frame) return false;
    memset(out_frame, 0, sizeof(*out_frame));

    char exp_crc[9] = {0}, act_crc[9] = {0};
    if (!meter_verify_frame_crc(raw_line, line_len, exp_crc, act_crc)) {
        strncpy(out_error_code, "CRC_MISMATCH", 31);
        return false;
    }

    /* Parse JSON */
    cJSON *root = cJSON_ParseWithLength(raw_line, line_len);
    if (!root) {
        strncpy(out_error_code, "MALFORMED_JSON", 31);
        return false;
    }

    const cJSON *proto = cJSON_GetObjectItemCaseSensitive(root, "protocol");
    if (!cJSON_IsString(proto) || strcmp(proto->valuestring, METER_PROTOCOL) != 0) {
        cJSON_Delete(root);
        strncpy(out_error_code, "UNSUPPORTED_VERSION", 31);
        return false;
    }
    strncpy(out_frame->protocol, proto->valuestring, sizeof(out_frame->protocol)-1);

    const cJSON *seq = cJSON_GetObjectItemCaseSensitive(root, "sequence");
    if (!cJSON_IsNumber(seq) || seq->valuedouble < 0 || seq->valuedouble > 4294967295.0) {
        cJSON_Delete(root);
        strncpy(out_error_code, "SEQUENCE_INVALID", 31);
        return false;
    }
    out_frame->sequence = (uint32_t)seq->valuedouble;

    const cJSON *sent = cJSON_GetObjectItemCaseSensitive(root, "sent_at");
    if (!cJSON_IsString(sent) || !sent->valuestring) {
        cJSON_Delete(root);
        strncpy(out_error_code, "TIMESTAMP_INVALID", 31);
        return false;
    }
    int64_t sent_sec = 0;
    if (!meter_parse_rfc3339(sent->valuestring, &sent_sec)) {
        cJSON_Delete(root);
        strncpy(out_error_code, "TIMESTAMP_INVALID", 31);
        return false;
    }
    strncpy(out_frame->sent_at, sent->valuestring, sizeof(out_frame->sent_at)-1);

    const cJSON *payload = cJSON_GetObjectItemCaseSensitive(root, "payload");
    if (!payload || !cJSON_IsObject(payload)) {
        cJSON_Delete(root);
        strncpy(out_error_code, "PAYLOAD_INVALID", 31);
        return false;
    }

    const cJSON *usage = cJSON_GetObjectItemCaseSensitive(payload, "usage");
    if (usage && cJSON_IsArray(usage)) {
        const cJSON *snap_item = NULL;
        cJSON_ArrayForEach(snap_item, usage) {
            if (out_frame->usage_count >= METER_MAX_SNAPSHOTS) break;
            if (!parse_snapshot_obj(snap_item, &out_frame->usage[out_frame->usage_count], out_error_code)) {
                cJSON_Delete(root);
                return false;
            }
            out_frame->usage_count++;
        }
    }

    const cJSON *resets = cJSON_GetObjectItemCaseSensitive(payload, "global_resets");
    if (resets && cJSON_IsArray(resets)) {
        const cJSON *r_item = NULL;
        cJSON_ArrayForEach(r_item, resets) {
            if (out_frame->global_reset_count >= METER_MAX_GLOBAL_RESETS) break;
            if (!parse_global_reset_obj(r_item, &out_frame->global_resets[out_frame->global_reset_count], out_error_code)) {
                cJSON_Delete(root);
                return false;
            }
            out_frame->global_reset_count++;
        }
    }

    cJSON_Delete(root);
    return true;
}

bool meter_parse_legacy_request(const char *json_str, meter_legacy_request_t *out_req)
{
    if (!json_str || !out_req) return false;
    memset(out_req, 0, sizeof(*out_req));

    cJSON *root = cJSON_Parse(json_str);
    if (!root) return false;

    const cJSON *src = cJSON_GetObjectItemCaseSensitive(root, "source");
    if (src && cJSON_IsString(src)) strncpy(out_req->source, src->valuestring, sizeof(out_req->source)-1);

    const cJSON *events = cJSON_GetObjectItemCaseSensitive(root, "events");
    if (events && cJSON_IsArray(events)) {
        const cJSON *ev_item = NULL;
        cJSON_ArrayForEach(ev_item, events) {
            if (out_req->event_count >= 8) break;
            meter_legacy_event_t *ev = &out_req->events[out_req->event_count];
            memset(ev, 0, sizeof(*ev));

            const cJSON *now = cJSON_GetObjectItemCaseSensitive(ev_item, "now");
            if (now && cJSON_IsString(now)) {
                strncpy(ev->now, now->valuestring, sizeof(ev->now)-1);
                meter_parse_rfc3339(ev->now, &ev->now_seconds);
            }

            const cJSON *err = cJSON_GetObjectItemCaseSensitive(ev_item, "error");
            if (err && cJSON_IsString(err)) strncpy(ev->error, err->valuestring, sizeof(ev->error)-1);

            const cJSON *body = cJSON_GetObjectItemCaseSensitive(ev_item, "body");
            if (body && !cJSON_IsNull(body)) {
                if (cJSON_IsString(body)) {
                    ev->body_raw = strdup(body->valuestring);
                } else {
                    ev->body_raw = cJSON_PrintUnformatted(body);
                }
            } else {
                ev->body_raw = NULL;
            }

            out_req->event_count++;
        }
    }

    cJSON_Delete(root);
    return true;
}

void meter_free_legacy_request(meter_legacy_request_t *req)
{
    if (!req) return;
    for (size_t i = 0; i < req->event_count; ++i) {
        if (req->events[i].body_raw) {
            free(req->events[i].body_raw);
            req->events[i].body_raw = NULL;
        }
    }
}
