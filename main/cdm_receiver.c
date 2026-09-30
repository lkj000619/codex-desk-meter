#include "cdm_receiver.h"

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "cJSON.h"

#define CDM_MAX_LINE 65536u

typedef struct {
    CdmUsage usage[CDM_MAX_USAGE];
    CdmGlobalReset global_resets[CDM_MAX_GLOBAL_RESETS];
} CdmParsedState;

static bool copy_string(char *target, size_t capacity, const cJSON *value, bool nullable) {
    if (cJSON_IsNull(value) && nullable) {
        target[0] = '\0';
        return true;
    }
    if (!cJSON_IsString(value) || value->valuestring == NULL) return false;
    size_t length = strlen(value->valuestring);
    if (length == 0 || length >= capacity) return false;
    memcpy(target, value->valuestring, length + 1);
    return true;
}

static bool is_percent(const cJSON *value, double *out, bool *present) {
    if (cJSON_IsNull(value)) {
        *present = false;
        *out = 0;
        return true;
    }
    if (!cJSON_IsNumber(value) || value->valuedouble < 0 || value->valuedouble > 100) return false;
    *present = true;
    *out = value->valuedouble;
    return true;
}

static bool is_nonnegative_number_or_null(const cJSON *value) {
    return cJSON_IsNull(value) || (cJSON_IsNumber(value) && value->valuedouble >= 0);
}

static bool is_optional_timestamp(const cJSON *value, int64_t *epoch_out) {
    if (cJSON_IsNull(value)) {
        if (epoch_out != NULL) *epoch_out = 0;
        return true;
    }
    if (!cJSON_IsString(value)) return false;
    int64_t epoch;
    if (!cdm_parse_epoch(value->valuestring, &epoch)) return false;
    if (epoch_out != NULL) *epoch_out = epoch;
    return true;
}

static bool object_keys_sorted(const cJSON *object) {
    if (!cJSON_IsObject(object)) return true;
    const char *previous = NULL;
    for (const cJSON *child = object->child; child != NULL; child = child->next) {
        if (previous != NULL && strcmp(previous, child->string) >= 0) return false;
        previous = child->string;
        if (cJSON_IsObject(child) && !object_keys_sorted(child)) return false;
        if (cJSON_IsArray(child)) {
            for (const cJSON *item = child->child; item != NULL; item = item->next) {
                if (cJSON_IsObject(item) && !object_keys_sorted(item)) return false;
            }
        }
    }
    return true;
}

uint32_t cdm_crc32(const unsigned char *data, size_t length) {
    uint32_t crc = 0xFFFFFFFFu;
    for (size_t i = 0; i < length; ++i) {
        crc ^= data[i];
        for (unsigned bit = 0; bit < 8; ++bit) {
            uint32_t mask = (uint32_t)-(int32_t)(crc & 1u);
            crc = (crc >> 1) ^ (0xEDB88320u & mask);
        }
    }
    return ~crc;
}

bool cdm_sequence_is_newer(uint32_t candidate, uint32_t current) {
    uint32_t difference = candidate - current;
    return difference != 0u && difference < 0x80000000u;
}

static bool leap_year(int year) {
    return (year % 4 == 0 && year % 100 != 0) || year % 400 == 0;
}

static int64_t days_from_civil(int year, unsigned month, unsigned day) {
    year -= month <= 2;
    int era = (year >= 0 ? year : year - 399) / 400;
    unsigned yoe = (unsigned)(year - era * 400);
    unsigned doy = (153u * (month + (month > 2 ? (unsigned)-3 : 9u)) + 2u) / 5u + day - 1u;
    unsigned doe = yoe * 365u + yoe / 4u - yoe / 100u + doy;
    return (int64_t)era * 146097 + (int64_t)doe - 719468;
}

bool cdm_epoch_to_utc(int64_t epoch, CdmCalendar *out) {
    if (out == NULL || epoch < 0) return false;
    int64_t days = epoch / 86400;
    int64_t day_seconds = epoch % 86400;
    int64_t z = days + 719468;
    int64_t era = (z >= 0 ? z : z - 146096) / 146097;
    unsigned doe = (unsigned)(z - era * 146097);
    unsigned yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
    int year = (int)yoe + (int)(era * 400);
    unsigned doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    unsigned mp = (5 * doy + 2) / 153;
    unsigned day = doy - (153 * mp + 2) / 5 + 1;
    unsigned month = mp + (mp < 10 ? 3 : (unsigned)-9);
    year += month <= 2;
    out->year = year;
    out->month = (int)month;
    out->day = (int)day;
    out->hour = (int)(day_seconds / 3600);
    out->minute = (int)((day_seconds % 3600) / 60);
    out->second = (int)(day_seconds % 60);
    return year >= 1970 && year <= 2199;
}

bool cdm_bcd_to_decimal(uint8_t bcd, uint8_t max_value, uint8_t *value_out) {
    uint8_t low = bcd & 0x0Fu;
    uint8_t high = (bcd >> 4) & 0x0Fu;
    if (value_out == NULL || low > 9 || high > 9) return false;
    uint8_t value = (uint8_t)(high * 10 + low);
    if (value > max_value) return false;
    *value_out = value;
    return true;
}

bool cdm_parse_epoch(const char *value, int64_t *epoch_out) {
    if (value == NULL || epoch_out == NULL || strlen(value) < 20) return false;
    int year, month, day, hour, minute, second, consumed = 0;
    if (sscanf(value, "%4d-%2d-%2dT%2d:%2d:%2d%n", &year, &month, &day, &hour, &minute, &second, &consumed) != 6) return false;
    if (year < 1970 || year > 2199 || month < 1 || month > 12 || hour > 23 || minute > 59 || second > 60) return false;
    static const unsigned days_by_month[] = {31,28,31,30,31,30,31,31,30,31,30,31};
    unsigned last_day = days_by_month[month - 1] + (month == 2 && leap_year(year));
    if (day < 1 || (unsigned)day > last_day) return false;
    const char *tail = value + consumed;
    int offset_seconds = 0;
    if (*tail == '.') {
        ++tail;
        if (!isdigit((unsigned char)*tail)) return false;
        while (isdigit((unsigned char)*tail)) ++tail;
    }
    if (*tail == 'Z' && tail[1] == '\0') {
        offset_seconds = 0;
    } else if ((*tail == '+' || *tail == '-') && strlen(tail) == 6 && tail[3] == ':') {
        int offset_hour, offset_minute;
        if (sscanf(tail + 1, "%2d:%2d", &offset_hour, &offset_minute) != 2 || offset_hour > 23 || offset_minute > 59) return false;
        offset_seconds = (offset_hour * 60 + offset_minute) * 60;
        if (*tail == '-') offset_seconds = -offset_seconds;
    } else {
        return false;
    }
    *epoch_out = days_from_civil(year, (unsigned)month, (unsigned)day) * 86400 + hour * 3600 + minute * 60 + second - offset_seconds;
    return true;
}

static bool crc_matches(const char *json, size_t length, const cJSON *root) {
    const cJSON *integrity = cJSON_GetObjectItemCaseSensitive(root, "integrity");
    const cJSON *algorithm = cJSON_GetObjectItemCaseSensitive(integrity, "algorithm");
    const cJSON *value = cJSON_GetObjectItemCaseSensitive(integrity, "value");
    if (!cJSON_IsObject(integrity) || cJSON_GetArraySize(integrity) != 2 || !cJSON_IsString(algorithm) ||
        strcmp(algorithm->valuestring, "crc32") != 0 || !cJSON_IsString(value) || strlen(value->valuestring) != 8) return false;
    char *integrity_start = strstr(json, "\"integrity\":{");
    if (integrity_start == NULL) return false;
    const char *member_start = integrity_start + strlen("\"integrity\":{");
    int depth = 1;
    bool in_string = false, escaped = false;
    const char *cursor = member_start;
    for (; (size_t)(cursor - json) < length; ++cursor) {
        char c = *cursor;
        if (in_string) {
            if (escaped) escaped = false;
            else if (c == '\\') escaped = true;
            else if (c == '"') in_string = false;
            continue;
        }
        if (c == '"') in_string = true;
        else if (c == '{') ++depth;
        else if (c == '}' && --depth == 0) break;
    }
    if ((size_t)(cursor - json) >= length || cursor[1] != ',') return false;
    const char *final_brace = json + length - 1;
    if (*final_brace != '}') return false;
    size_t rest_length = (size_t)(final_brace - (cursor + 2));
    char *body = malloc(rest_length + 3);
    if (body == NULL) return false;
    body[0] = '{';
    memcpy(body + 1, cursor + 2, rest_length);
    body[rest_length + 1] = '}';
    body[rest_length + 2] = '\0';
    unsigned long expected = strtoul(value->valuestring, NULL, 16);
    uint32_t actual = cdm_crc32((const unsigned char *)body, rest_length + 2);
    free(body);
    return actual == (uint32_t)expected;
}

static bool exact_keys(const cJSON *object, const char *const *keys, size_t count) {
    if (!cJSON_IsObject(object) || (size_t)cJSON_GetArraySize(object) != count) return false;
    for (size_t i = 0; i < count; ++i) if (cJSON_GetObjectItemCaseSensitive(object, keys[i]) == NULL) return false;
    return true;
}

static bool parse_usage(const cJSON *item, CdmUsage *out) {
    static const char *const required[] = {"schema_version", "snapshot_id", "provider_id", "agent_id", "host_id",
        "model_id", "account_profile_id", "source_kind", "metric_kind", "unit", "status", "observed_at",
        "windows", "stale", "last_good_at", "error_code", "error_reason"};
    if (!exact_keys(item, required, sizeof(required) / sizeof(required[0]))) return false;
    const cJSON *version = cJSON_GetObjectItemCaseSensitive(item, "schema_version");
    const cJSON *windows = cJSON_GetObjectItemCaseSensitive(item, "windows");
    const cJSON *stale = cJSON_GetObjectItemCaseSensitive(item, "stale");
    if (!cJSON_IsNumber(version) || version->valueint != 1 || !cJSON_IsArray(windows) ||
        !cJSON_IsBool(stale) || cJSON_GetArraySize(windows) > CDM_MAX_WINDOWS) return false;
    const cJSON *source_kind = cJSON_GetObjectItemCaseSensitive(item, "source_kind");
    const cJSON *metric_kind = cJSON_GetObjectItemCaseSensitive(item, "metric_kind");
    const cJSON *snapshot_unit = cJSON_GetObjectItemCaseSensitive(item, "unit");
    const char *source_kinds[] = {"fixture", "local_runtime", "provider_api", "ide_telemetry", "unknown"};
    const char *metric_kinds[] = {"quota_window", "token_balance", "credits", "session_telemetry"};
    const char *units[] = {"percent", "token", "credit", "unknown"};
    bool source_valid = false, metric_valid = false, unit_valid = false;
    if (!cJSON_IsString(source_kind) || !cJSON_IsString(metric_kind) || !cJSON_IsString(snapshot_unit)) return false;
    for (size_t i = 0; i < sizeof(source_kinds)/sizeof(source_kinds[0]); ++i) source_valid |= strcmp(source_kind->valuestring, source_kinds[i]) == 0;
    for (size_t i = 0; i < sizeof(metric_kinds)/sizeof(metric_kinds[0]); ++i) metric_valid |= strcmp(metric_kind->valuestring, metric_kinds[i]) == 0;
    for (size_t i = 0; i < sizeof(units)/sizeof(units[0]); ++i) unit_valid |= strcmp(snapshot_unit->valuestring, units[i]) == 0;
    if (!source_valid || !metric_valid || !unit_valid) return false;
    if (!copy_string(out->provider_id, sizeof(out->provider_id), cJSON_GetObjectItemCaseSensitive(item, "provider_id"), false) ||
        !copy_string(out->status, sizeof(out->status), cJSON_GetObjectItemCaseSensitive(item, "status"), false)) return false;
    const cJSON *agent = cJSON_GetObjectItemCaseSensitive(item, "agent_id");
    const cJSON *host = cJSON_GetObjectItemCaseSensitive(item, "host_id");
    if (!copy_string(out->agent_id, sizeof(out->agent_id), agent, true) || !copy_string(out->host_id, sizeof(out->host_id), host, true)) return false;
    const cJSON *observed = cJSON_GetObjectItemCaseSensitive(item, "observed_at");
    if (!copy_string(out->observed_at, sizeof(out->observed_at), observed, true) || !is_optional_timestamp(observed, NULL)) return false;
    const cJSON *error = cJSON_GetObjectItemCaseSensitive(item, "error_code");
    const cJSON *reason = cJSON_GetObjectItemCaseSensitive(item, "error_reason");
    if (!copy_string(out->error_code, sizeof(out->error_code), error, true) || !copy_string(out->error_reason, sizeof(out->error_reason), reason, true)) return false;
    const cJSON *last_good = cJSON_GetObjectItemCaseSensitive(item, "last_good_at");
    if (!is_optional_timestamp(last_good, &out->last_good_epoch)) return false;
    out->stale = cJSON_IsTrue(stale);
    out->window_count = 0;
    const char *allowed_status[] = {"available", "unavailable", "unsupported", "unauthorized", "error", "stale"};
    bool found_status = false;
    for (size_t i = 0; i < sizeof(allowed_status) / sizeof(allowed_status[0]); ++i) found_status |= strcmp(out->status, allowed_status[i]) == 0;
    if (!found_status || (strcmp(out->status, "stale") == 0 && !out->stale)) return false;
    if (strcmp(out->status, "available") != 0 && (out->error_code[0] == '\0' || out->error_reason[0] == '\0')) return false;
    for (const cJSON *source_window = windows->child; source_window != NULL; source_window = source_window->next) {
        static const char *const window_keys[] = {"window_id", "label", "used_units", "remaining_units", "limit_units", "unit", "percent_used", "percent_remaining", "resets_at"};
        int key_count = cJSON_GetArraySize(source_window);
        if (!cJSON_IsObject(source_window) || (key_count != 9 && key_count != 10)) return false;
        for (size_t k = 0; k < sizeof(window_keys)/sizeof(window_keys[0]); ++k)
            if (cJSON_GetObjectItemCaseSensitive(source_window, window_keys[k]) == NULL) return false;
        CdmWindow *window = &out->windows[out->window_count];
        if (!copy_string(window->window_id, sizeof(window->window_id), cJSON_GetObjectItemCaseSensitive(source_window, "window_id"), false) ||
            !copy_string(window->label, sizeof(window->label), cJSON_GetObjectItemCaseSensitive(source_window, "label"), false) ||
            !copy_string(window->unit, sizeof(window->unit), cJSON_GetObjectItemCaseSensitive(source_window, "unit"), false)) return false;
        bool window_unit_valid = false;
        for (size_t u = 0; u < sizeof(units)/sizeof(units[0]); ++u) window_unit_valid |= strcmp(window->unit, units[u]) == 0;
        if (!window_unit_valid ||
            !is_nonnegative_number_or_null(cJSON_GetObjectItemCaseSensitive(source_window, "used_units")) ||
            !is_nonnegative_number_or_null(cJSON_GetObjectItemCaseSensitive(source_window, "remaining_units")) ||
            !is_nonnegative_number_or_null(cJSON_GetObjectItemCaseSensitive(source_window, "limit_units"))) return false;
        if (!is_percent(cJSON_GetObjectItemCaseSensitive(source_window, "percent_used"), &window->percent_used, &window->has_percent_used) ||
            !is_percent(cJSON_GetObjectItemCaseSensitive(source_window, "percent_remaining"), &window->percent_remaining, &window->has_percent_remaining)) return false;
        const cJSON *resets_at = cJSON_GetObjectItemCaseSensitive(source_window, "resets_at");
        if (!copy_string(window->resets_at, sizeof(window->resets_at), resets_at, true) || !is_optional_timestamp(resets_at, NULL)) return false;
        const cJSON *reset_status = cJSON_GetObjectItemCaseSensitive(source_window, "reset_status");
        if (reset_status == NULL) strcpy(window->reset_status, "unknown");
        else if (!copy_string(window->reset_status, sizeof(window->reset_status), reset_status, false)) return false;
        if (strcmp(window->reset_status, "unknown") != 0 && strcmp(window->reset_status, "scheduled") != 0 && strcmp(window->reset_status, "expired") != 0) return false;
        ++out->window_count;
    }
    return true;
}

static bool parse_global_reset(const cJSON *item, CdmGlobalReset *out) {
    static const char *const required[] = {"schema_version", "source", "captured_at", "latest_reset_at",
        "forecast_24h_percent", "forecast_48h_percent", "forecast_is_schedule", "stale", "error_code"};
    if (!exact_keys(item, required, sizeof(required) / sizeof(required[0]))) return false;
    const cJSON *version = cJSON_GetObjectItemCaseSensitive(item, "schema_version");
    const cJSON *schedule = cJSON_GetObjectItemCaseSensitive(item, "forecast_is_schedule");
    const cJSON *stale = cJSON_GetObjectItemCaseSensitive(item, "stale");
    if (!cJSON_IsNumber(version) || version->valueint != 1 || !cJSON_IsFalse(schedule) || !cJSON_IsBool(stale)) return false;
    if (!copy_string(out->source, sizeof(out->source), cJSON_GetObjectItemCaseSensitive(item, "source"), false) ||
        !copy_string(out->captured_at, sizeof(out->captured_at), cJSON_GetObjectItemCaseSensitive(item, "captured_at"), false)) return false;
    if (!cdm_parse_epoch(out->captured_at, &out->captured_epoch)) return false;
    const cJSON *latest = cJSON_GetObjectItemCaseSensitive(item, "latest_reset_at");
    if (!copy_string(out->latest_reset_at, sizeof(out->latest_reset_at), latest, true) || !is_optional_timestamp(latest, NULL)) return false;
    out->has_latest_reset = out->latest_reset_at[0] != '\0';
    out->stale = cJSON_IsTrue(stale);
    const cJSON *forecast_24 = cJSON_GetObjectItemCaseSensitive(item, "forecast_24h_percent");
    const cJSON *forecast_48 = cJSON_GetObjectItemCaseSensitive(item, "forecast_48h_percent");
    double ignored;
    bool has_value;
    if (!is_percent(forecast_24, &ignored, &has_value) || !is_percent(forecast_48, &ignored, &has_value)) return false;
    if (!copy_string(out->error_code, sizeof(out->error_code), cJSON_GetObjectItemCaseSensitive(item, "error_code"), true)) return false;
    return strcmp(out->source, "codex-resets.com") == 0 || strcmp(out->source, "codex-reset.com") == 0;
}

void cdm_receiver_init(CdmReceiver *receiver) {
    memset(receiver, 0, sizeof(*receiver));
}

CdmResult cdm_receiver_apply(CdmReceiver *receiver, const char *json, size_t length, int64_t now_epoch) {
    if (receiver == NULL || json == NULL || length == 0 || length > CDM_MAX_LINE) return CDM_REJECT_SCHEMA;
    cJSON *root = cJSON_ParseWithLength(json, length);
    if (root == NULL) { receiver->last_error = CDM_REJECT_JSON; return CDM_REJECT_JSON; }
    char *printed = cJSON_PrintUnformatted(root);
    bool canonical = printed != NULL && strlen(printed) == length && memcmp(printed, json, length) == 0 && object_keys_sorted(root);
    if (printed != NULL) cJSON_free(printed);
    if (!canonical) { cJSON_Delete(root); receiver->last_error = CDM_REJECT_CANONICAL; return CDM_REJECT_CANONICAL; }
    static const char *const root_keys[] = {"integrity", "payload", "protocol", "sent_at", "sequence"};
    static const char *const payload_keys[] = {"global_resets", "usage"};
    if (!exact_keys(root, root_keys, sizeof(root_keys) / sizeof(root_keys[0]))) {
        cJSON_Delete(root); receiver->last_error = CDM_REJECT_SCHEMA; return CDM_REJECT_SCHEMA;
    }
    const cJSON *protocol = cJSON_GetObjectItemCaseSensitive(root, "protocol");
    if (!cJSON_IsString(protocol) || strcmp(protocol->valuestring, "cdm/1") != 0) {
        cJSON_Delete(root); receiver->last_error = CDM_REJECT_VERSION; return CDM_REJECT_VERSION;
    }
    const cJSON *sequence = cJSON_GetObjectItemCaseSensitive(root, "sequence");
    const cJSON *sent_at = cJSON_GetObjectItemCaseSensitive(root, "sent_at");
    int64_t sent_epoch;
    if (!cJSON_IsNumber(sequence) || sequence->valuedouble < 0 || sequence->valuedouble > 4294967295.0 ||
        (double)sequence->valueint != sequence->valuedouble || !cJSON_IsString(sent_at) ||
        !cdm_parse_epoch(sent_at->valuestring, &sent_epoch) ||
        (now_epoch >= 1704067200 && sent_epoch > now_epoch + 5)) {
        cJSON_Delete(root); receiver->last_error = CDM_REJECT_SCHEMA; return CDM_REJECT_SCHEMA;
    }
    if (!crc_matches(json, length, root)) { cJSON_Delete(root); receiver->last_error = CDM_REJECT_CRC; return CDM_REJECT_CRC; }
    uint32_t sequence_value = (uint32_t)sequence->valuedouble;
    if (receiver->has_sequence && !cdm_sequence_is_newer(sequence_value, receiver->sequence)) {
        cJSON_Delete(root); receiver->last_error = CDM_REJECT_SEQUENCE; return CDM_REJECT_SEQUENCE;
    }
    const cJSON *payload = cJSON_GetObjectItemCaseSensitive(root, "payload");
    const cJSON *usage = cJSON_GetObjectItemCaseSensitive(payload, "usage");
    const cJSON *resets = cJSON_GetObjectItemCaseSensitive(payload, "global_resets");
    if (!exact_keys(payload, payload_keys, sizeof(payload_keys) / sizeof(payload_keys[0])) || !cJSON_IsArray(usage) ||
        !cJSON_IsArray(resets) || cJSON_GetArraySize(usage) > CDM_MAX_USAGE || cJSON_GetArraySize(resets) > CDM_MAX_GLOBAL_RESETS) {
        cJSON_Delete(root); receiver->last_error = CDM_REJECT_CAPACITY; return CDM_REJECT_CAPACITY;
    }
    CdmParsedState *parsed = calloc(1, sizeof(*parsed));
    if (parsed == NULL) {
        cJSON_Delete(root); receiver->last_error = CDM_REJECT_CAPACITY; return CDM_REJECT_CAPACITY;
    }
    size_t usage_count = 0, reset_count = 0;
    for (const cJSON *item = usage->child; item != NULL; item = item->next) {
        if (!parse_usage(item, &parsed->usage[usage_count++])) {
            free(parsed); cJSON_Delete(root); receiver->last_error = CDM_REJECT_SCHEMA; return CDM_REJECT_SCHEMA;
        }
    }
    for (const cJSON *item = resets->child; item != NULL; item = item->next) {
        if (!parse_global_reset(item, &parsed->global_resets[reset_count++])) {
            free(parsed); cJSON_Delete(root); receiver->last_error = CDM_REJECT_SCHEMA; return CDM_REJECT_SCHEMA;
        }
    }
    cJSON_Delete(root);
    memcpy(receiver->usage, parsed->usage, sizeof(receiver->usage));
    memcpy(receiver->global_resets, parsed->global_resets, sizeof(receiver->global_resets));
    receiver->usage_count = usage_count;
    receiver->reset_count = reset_count;
    free(parsed);
    receiver->sequence = sequence_value;
    receiver->has_sequence = true;
    receiver->has_good_frame = true;
    receiver->last_good_epoch = sent_epoch;
    receiver->stale = now_epoch >= 1704067200 && now_epoch - sent_epoch >= 300;
    receiver->last_error = CDM_ACCEPTED;
    return CDM_ACCEPTED;
}

void cdm_receiver_update_stale(CdmReceiver *receiver, int64_t now_epoch) {
    if (receiver == NULL || !receiver->has_good_frame) return;
    receiver->stale = now_epoch >= 1704067200 && now_epoch - receiver->last_good_epoch >= 300;
    for (size_t i = 0; i < receiver->usage_count; ++i) {
        const CdmUsage *usage = &receiver->usage[i];
        if (usage->stale || (strcmp(usage->status, "available") == 0 && usage->last_good_epoch > 0 &&
            now_epoch >= usage->last_good_epoch && now_epoch - usage->last_good_epoch >= 300)) receiver->stale = true;
    }
    for (size_t i = 0; i < receiver->reset_count; ++i) {
        const CdmGlobalReset *reset = &receiver->global_resets[i];
        if (reset->stale || (now_epoch >= reset->captured_epoch && now_epoch - reset->captured_epoch >= 300)) receiver->stale = true;
    }
}

CdmScreen cdm_screen_next(CdmScreen current) {
    if (current == CDM_SCREEN_DASHBOARD) return CDM_SCREEN_GLOBAL_RESET;
    if (current == CDM_SCREEN_GLOBAL_RESET) return CDM_SCREEN_STATUS;
    return CDM_SCREEN_DASHBOARD;
}

bool cdm_button_update(CdmButtonDebouncer *button, bool raw_pressed, uint32_t now_ms, uint32_t debounce_ms) {
    if (button == NULL) return false;
    if (!button->initialized) {
        button->candidate_pressed = raw_pressed;
        button->candidate_since_ms = now_ms;
        button->initialized = true;
        return false;
    }
    if (raw_pressed != button->candidate_pressed) {
        button->candidate_pressed = raw_pressed;
        button->candidate_since_ms = now_ms;
        return false;
    }
    if (button->stable_pressed != button->candidate_pressed && (uint32_t)(now_ms - button->candidate_since_ms) >= debounce_ms) {
        button->stable_pressed = button->candidate_pressed;
        return true;
    }
    return false;
}

size_t cdm_dashboard_page(size_t total_windows, uint64_t elapsed_seconds) {
    size_t pages = (total_windows + 7u) / 8u;
    return pages == 0 ? 0 : (size_t)((elapsed_seconds / 8u) % pages);
}
