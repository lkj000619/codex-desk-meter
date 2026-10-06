#include "meter_core.h"

#include <ctype.h>
#include <inttypes.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum { J_NULL, J_BOOL, J_NUMBER, J_STRING, J_OBJECT, J_ARRAY };

typedef struct {
    int type;
    int first;
    int next;
    size_t key_offset;
    size_t key_length;
    size_t text_offset;
    size_t text_length;
    size_t raw_start;
    size_t raw_end;
} jnode_t;

typedef struct {
    const uint8_t *raw;
    size_t raw_length;
    size_t pos;
    jnode_t *nodes;
    size_t node_count;
    size_t node_capacity;
    char *strings;
    size_t string_pos;
    size_t string_capacity;
    char error[40];
} jdoc_t;

static jdoc_t *sort_doc;

static void set_error(meter_receiver_t *receiver, const char *code)
{
    if (!receiver) return;
    snprintf(receiver->last_error, sizeof(receiver->last_error), "%s", code);
}

static void skip_ws(jdoc_t *doc)
{
    while (doc->pos < doc->raw_length) {
        uint8_t c = doc->raw[doc->pos];
        if (c != ' ' && c != '\t' && c != '\r' && c != '\n') break;
        doc->pos++;
    }
}

static int hex_value(uint8_t c)
{
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}

static bool append_utf8(jdoc_t *doc, uint32_t cp)
{
    uint8_t encoded[4];
    size_t count;
    if (cp <= 0x7f) {
        encoded[0] = (uint8_t)cp;
        count = 1;
    } else if (cp <= 0x7ff) {
        encoded[0] = (uint8_t)(0xc0 | (cp >> 6));
        encoded[1] = (uint8_t)(0x80 | (cp & 0x3f));
        count = 2;
    } else if (cp <= 0xffff && !(cp >= 0xd800 && cp <= 0xdfff)) {
        encoded[0] = (uint8_t)(0xe0 | (cp >> 12));
        encoded[1] = (uint8_t)(0x80 | ((cp >> 6) & 0x3f));
        encoded[2] = (uint8_t)(0x80 | (cp & 0x3f));
        count = 3;
    } else if (cp <= 0x10ffff) {
        encoded[0] = (uint8_t)(0xf0 | (cp >> 18));
        encoded[1] = (uint8_t)(0x80 | ((cp >> 12) & 0x3f));
        encoded[2] = (uint8_t)(0x80 | ((cp >> 6) & 0x3f));
        encoded[3] = (uint8_t)(0x80 | (cp & 0x3f));
        count = 4;
    } else {
        return false;
    }
    if (doc->string_pos + count >= doc->string_capacity) return false;
    memcpy(doc->strings + doc->string_pos, encoded, count);
    doc->string_pos += count;
    return true;
}

static bool read_hex4(jdoc_t *doc, uint32_t *value)
{
    if (doc->pos + 4 > doc->raw_length) return false;
    uint32_t result = 0;
    for (int i = 0; i < 4; i++) {
        int digit = hex_value(doc->raw[doc->pos++]);
        if (digit < 0) return false;
        result = (result << 4) | (uint32_t)digit;
    }
    *value = result;
    return true;
}

static bool copy_raw_utf8(jdoc_t *doc)
{
    uint8_t first = doc->raw[doc->pos];
    uint32_t cp;
    size_t count;
    if (first < 0x80) {
        cp = first;
        count = 1;
    } else if (first >= 0xc2 && first <= 0xdf) {
        cp = first & 0x1f;
        count = 2;
    } else if (first >= 0xe0 && first <= 0xef) {
        cp = first & 0x0f;
        count = 3;
    } else if (first >= 0xf0 && first <= 0xf4) {
        cp = first & 0x07;
        count = 4;
    } else {
        return false;
    }
    if (doc->pos + count > doc->raw_length) return false;
    for (size_t i = 1; i < count; i++) {
        uint8_t c = doc->raw[doc->pos + i];
        if ((c & 0xc0) != 0x80) return false;
        if (i == 1 && ((first == 0xe0 && c < 0xa0) ||
                       (first == 0xed && c >= 0xa0) ||
                       (first == 0xf0 && c < 0x90) ||
                       (first == 0xf4 && c >= 0x90))) return false;
        cp = (cp << 6) | (c & 0x3f);
    }
    if (doc->string_pos + count >= doc->string_capacity) return false;
    memcpy(doc->strings + doc->string_pos, doc->raw + doc->pos, count);
    doc->string_pos += count;
    doc->pos += count;
    (void)cp;
    return true;
}

static bool parse_string(jdoc_t *doc, size_t *offset, size_t *length)
{
    if (doc->pos >= doc->raw_length || doc->raw[doc->pos++] != '"') return false;
    *offset = doc->string_pos;
    while (doc->pos < doc->raw_length) {
        uint8_t c = doc->raw[doc->pos++];
        if (c == '"') {
            *length = doc->string_pos - *offset;
            if (doc->string_pos >= doc->string_capacity) return false;
            doc->strings[doc->string_pos++] = '\0';
            return true;
        }
        if (c < 0x20) return false;
        if (c == '\\') {
            if (doc->pos >= doc->raw_length) return false;
            uint8_t escape = doc->raw[doc->pos++];
            switch (escape) {
            case '"': case '\\': case '/':
                if (!append_utf8(doc, escape)) return false;
                break;
            case 'b': if (!append_utf8(doc, '\b')) return false; break;
            case 'f': if (!append_utf8(doc, '\f')) return false; break;
            case 'n': if (!append_utf8(doc, '\n')) return false; break;
            case 'r': if (!append_utf8(doc, '\r')) return false; break;
            case 't': if (!append_utf8(doc, '\t')) return false; break;
            case 'u': {
                uint32_t cp;
                if (!read_hex4(doc, &cp)) return false;
                if (cp >= 0xd800 && cp <= 0xdbff) {
                    uint32_t low;
                    if (doc->pos + 2 > doc->raw_length || doc->raw[doc->pos++] != '\\' ||
                        doc->raw[doc->pos++] != 'u' || !read_hex4(doc, &low) ||
                        low < 0xdc00 || low > 0xdfff) return false;
                    cp = 0x10000 + ((cp - 0xd800) << 10) + (low - 0xdc00);
                } else if (cp >= 0xdc00 && cp <= 0xdfff) {
                    return false;
                }
                if (!append_utf8(doc, cp)) return false;
                break;
            }
            default: return false;
            }
        } else if (c < 0x80) {
            if (!append_utf8(doc, c)) return false;
        } else {
            doc->pos--;
            if (!copy_raw_utf8(doc)) return false;
        }
    }
    return false;
}

static int add_node(jdoc_t *doc, int type, size_t raw_start)
{
    if (doc->node_count >= doc->node_capacity) return -1;
    int index = (int)doc->node_count++;
    jnode_t *node = &doc->nodes[index];
    memset(node, 0, sizeof(*node));
    node->type = type;
    node->first = -1;
    node->next = -1;
    node->raw_start = raw_start;
    return index;
}

static bool parse_value(jdoc_t *doc, int *index);

static bool parse_object(jdoc_t *doc, int index)
{
    doc->pos++;
    skip_ws(doc);
    int last = -1;
    if (doc->pos < doc->raw_length && doc->raw[doc->pos] == '}') {
        doc->pos++;
        doc->nodes[index].raw_end = doc->pos;
        return true;
    }
    while (doc->pos < doc->raw_length) {
        size_t key_offset, key_length;
        if (!parse_string(doc, &key_offset, &key_length)) return false;
        skip_ws(doc);
        if (doc->pos >= doc->raw_length || doc->raw[doc->pos++] != ':') return false;
        skip_ws(doc);
        int child;
        if (!parse_value(doc, &child)) return false;
        doc->nodes[child].key_offset = key_offset;
        doc->nodes[child].key_length = key_length;
        if (last < 0) doc->nodes[index].first = child;
        else doc->nodes[last].next = child;
        last = child;
        skip_ws(doc);
        if (doc->pos >= doc->raw_length) return false;
        uint8_t separator = doc->raw[doc->pos++];
        if (separator == '}') {
            doc->nodes[index].raw_end = doc->pos;
            return true;
        }
        if (separator != ',') return false;
        skip_ws(doc);
    }
    return false;
}

static bool parse_array(jdoc_t *doc, int index)
{
    doc->pos++;
    skip_ws(doc);
    int last = -1;
    if (doc->pos < doc->raw_length && doc->raw[doc->pos] == ']') {
        doc->pos++;
        doc->nodes[index].raw_end = doc->pos;
        return true;
    }
    while (doc->pos < doc->raw_length) {
        int child;
        if (!parse_value(doc, &child)) return false;
        if (last < 0) doc->nodes[index].first = child;
        else doc->nodes[last].next = child;
        last = child;
        skip_ws(doc);
        if (doc->pos >= doc->raw_length) return false;
        uint8_t separator = doc->raw[doc->pos++];
        if (separator == ']') {
            doc->nodes[index].raw_end = doc->pos;
            return true;
        }
        if (separator != ',') return false;
        skip_ws(doc);
    }
    return false;
}

static bool parse_number(jdoc_t *doc, int index)
{
    size_t start = doc->pos;
    if (doc->raw[doc->pos] == '-') doc->pos++;
    if (doc->pos >= doc->raw_length) return false;
    if (doc->raw[doc->pos] == '0') {
        doc->pos++;
        if (doc->pos < doc->raw_length && isdigit(doc->raw[doc->pos])) return false;
    } else {
        if (doc->raw[doc->pos] < '1' || doc->raw[doc->pos] > '9') return false;
        while (doc->pos < doc->raw_length && isdigit(doc->raw[doc->pos])) doc->pos++;
    }
    if (doc->pos < doc->raw_length && doc->raw[doc->pos] == '.') {
        doc->pos++;
        size_t fraction = doc->pos;
        while (doc->pos < doc->raw_length && isdigit(doc->raw[doc->pos])) doc->pos++;
        if (fraction == doc->pos) return false;
    }
    if (doc->pos < doc->raw_length && (doc->raw[doc->pos] == 'e' || doc->raw[doc->pos] == 'E')) {
        doc->pos++;
        if (doc->pos < doc->raw_length && (doc->raw[doc->pos] == '+' || doc->raw[doc->pos] == '-')) doc->pos++;
        size_t exponent = doc->pos;
        while (doc->pos < doc->raw_length && isdigit(doc->raw[doc->pos])) doc->pos++;
        if (exponent == doc->pos) return false;
    }
    if (doc->pos - start >= 64) return false;
    char number[64];
    memcpy(number, doc->raw + start, doc->pos - start);
    number[doc->pos - start] = '\0';
    char *end = NULL;
    double value = strtod(number, &end);
    if (!end || *end || !isfinite(value)) return false;
    doc->nodes[index].raw_start = start;
    doc->nodes[index].raw_end = doc->pos;
    return true;
}

static bool parse_value(jdoc_t *doc, int *index)
{
    skip_ws(doc);
    if (doc->pos >= doc->raw_length) return false;
    size_t start = doc->pos;
    uint8_t c = doc->raw[doc->pos];
    int type = c == '{' ? J_OBJECT : c == '[' ? J_ARRAY : c == '"' ? J_STRING :
               (c == '-' || isdigit(c)) ? J_NUMBER : (c == 't' || c == 'f') ? J_BOOL : J_NULL;
    int current = add_node(doc, type, start);
    if (current < 0) return false;
    *index = current;
    if (type == J_OBJECT) return parse_object(doc, current);
    if (type == J_ARRAY) return parse_array(doc, current);
    if (type == J_STRING) {
        if (!parse_string(doc, &doc->nodes[current].text_offset, &doc->nodes[current].text_length)) return false;
        doc->nodes[current].raw_end = doc->pos;
        return true;
    }
    if (type == J_NUMBER) return parse_number(doc, current);
    const char *literal = c == 't' ? "true" : c == 'f' ? "false" : "null";
    size_t length = strlen(literal);
    if (doc->pos + length > doc->raw_length || memcmp(doc->raw + doc->pos, literal, length) != 0) return false;
    if (type == J_BOOL) doc->nodes[current].text_length = c == 't' ? 1u : 0u;
    doc->pos += length;
    doc->nodes[current].raw_end = doc->pos;
    return true;
}

static bool doc_parse(jdoc_t *doc, const uint8_t *raw, size_t length)
{
    memset(doc, 0, sizeof(*doc));
    doc->raw = raw;
    doc->raw_length = length;
    doc->node_capacity = length / 2 + 4;
    doc->string_capacity = length + 1;
    doc->nodes = (jnode_t *)calloc(doc->node_capacity, sizeof(jnode_t));
    doc->strings = (char *)malloc(doc->string_capacity);
    if (!doc->nodes || !doc->strings) return false;
    int root;
    if (!parse_value(doc, &root)) return false;
    skip_ws(doc);
    return doc->pos == doc->raw_length && root == 0;
}

static void doc_free(jdoc_t *doc)
{
    free(doc->nodes);
    free(doc->strings);
    doc->nodes = NULL;
    doc->strings = NULL;
}

static bool key_equals(jdoc_t *doc, int node, const char *key)
{
    const jnode_t *value = &doc->nodes[node];
    size_t length = strlen(key);
    return value->key_length == length &&
           memcmp(doc->strings + value->key_offset, key, length) == 0;
}

static int object_get(jdoc_t *doc, int object, const char *key)
{
    if (object < 0 || doc->nodes[object].type != J_OBJECT) return -1;
    for (int child = doc->nodes[object].first; child >= 0; child = doc->nodes[child].next) {
        if (key_equals(doc, child, key)) return child;
    }
    return -1;
}

static const char *string_value(jdoc_t *doc, int node, size_t *length)
{
    if (node < 0 || doc->nodes[node].type != J_STRING) return NULL;
    if (length) *length = doc->nodes[node].text_length;
    return doc->strings + doc->nodes[node].text_offset;
}

static bool nullable_string(jdoc_t *doc, int node, const char **text, size_t *length)
{
    if (node < 0) return false;
    if (doc->nodes[node].type == J_NULL) {
        if (text) *text = NULL;
        if (length) *length = 0;
        return true;
    }
    const char *value = string_value(doc, node, length);
    if (!value) return false;
    if (text) *text = value;
    return true;
}

static bool string_is(jdoc_t *doc, int node, const char *value)
{
    size_t length;
    const char *text = string_value(doc, node, &length);
    return text && strlen(value) == length && memcmp(text, value, length) == 0;
}

static bool allowed_keys(jdoc_t *doc, int object, const char *const *allowed, size_t count)
{
    if (object < 0 || doc->nodes[object].type != J_OBJECT) return false;
    for (int child = doc->nodes[object].first; child >= 0; child = doc->nodes[child].next) {
        bool found = false;
        for (size_t i = 0; i < count; i++) {
            if (key_equals(doc, child, allowed[i])) { found = true; break; }
        }
        if (!found) return false;
        for (int prior = doc->nodes[object].first; prior != child; prior = doc->nodes[prior].next) {
            if (doc->nodes[prior].key_length == doc->nodes[child].key_length &&
                memcmp(doc->strings + doc->nodes[prior].key_offset,
                       doc->strings + doc->nodes[child].key_offset,
                       doc->nodes[child].key_length) == 0) return false;
        }
    }
    return true;
}

static bool all_required(jdoc_t *doc, int object, const char *const *required, size_t count)
{
    if (object < 0 || doc->nodes[object].type != J_OBJECT) return false;
    for (size_t i = 0; i < count; i++) if (object_get(doc, object, required[i]) < 0) return false;
    return true;
}

static int64_t days_from_civil(int year, unsigned month, unsigned day)
{
    year -= month <= 2;
    const int era = (year >= 0 ? year : year - 399) / 400;
    const unsigned yoe = (unsigned)(year - era * 400);
    const unsigned doy = (153 * (month + (month > 2 ? (unsigned)-3 : 9)) + 2) / 5 + day - 1;
    const unsigned doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
    return (int64_t)era * 146097 + (int64_t)doe - 719468;
}

static bool parse_digits(const char *text, size_t length, size_t offset, size_t count, int *value)
{
    if (offset + count > length) return false;
    int result = 0;
    for (size_t i = 0; i < count; i++) {
        if (text[offset + i] < '0' || text[offset + i] > '9') return false;
        result = result * 10 + text[offset + i] - '0';
    }
    *value = result;
    return true;
}

static bool parse_timestamp(const char *text, size_t length, int64_t *epoch)
{
    int year, month, day, hour, minute, second;
    if (length < 20 || !parse_digits(text, length, 0, 4, &year) || text[4] != '-' ||
        !parse_digits(text, length, 5, 2, &month) || text[7] != '-' ||
        !parse_digits(text, length, 8, 2, &day) || text[10] != 'T' ||
        !parse_digits(text, length, 11, 2, &hour) || text[13] != ':' ||
        !parse_digits(text, length, 14, 2, &minute) || text[16] != ':' ||
        !parse_digits(text, length, 17, 2, &second) || year < 1 || month < 1 || month > 12 ||
        hour > 23 || minute > 59 || second > 59) return false;
    static const int month_days[] = {31,28,31,30,31,30,31,31,30,31,30,31};
    int max_day = month_days[month - 1];
    bool leap = (year % 4 == 0 && year % 100 != 0) || year % 400 == 0;
    if (month == 2 && leap) max_day++;
    if (day < 1 || day > max_day) return false;
    size_t pos = 19;
    if (pos < length && text[pos] == '.') {
        pos++;
        size_t begin = pos;
        while (pos < length && text[pos] >= '0' && text[pos] <= '9') pos++;
        if (pos == begin) return false;
    }
    int offset_seconds = 0;
    if (pos < length && text[pos] == 'Z' && pos + 1 == length) {
        pos++;
    } else if (pos + 6 == length && (text[pos] == '+' || text[pos] == '-') && text[pos + 3] == ':') {
        int oh, om;
        if (!parse_digits(text, length, pos + 1, 2, &oh) ||
            !parse_digits(text, length, pos + 4, 2, &om) || oh > 23 || om > 59) return false;
        offset_seconds = (oh * 60 + om) * 60;
        if (text[pos] == '-') offset_seconds = -offset_seconds;
        pos += 6;
    } else {
        return false;
    }
    if (pos != length) return false;
    *epoch = days_from_civil(year, (unsigned)month, (unsigned)day) * 86400 +
             hour * 3600 + minute * 60 + second - offset_seconds;
    return true;
}

bool meter_timestamp_delta_seconds(const char *newer, const char *older, int64_t *delta_seconds)
{
    if (!newer || !older || !delta_seconds) return false;
    int64_t n, o;
    if (!parse_timestamp(newer, strlen(newer), &n) || !parse_timestamp(older, strlen(older), &o)) return false;
    *delta_seconds = n - o;
    return true;
}

bool meter_source_is_stale(const char *frame_sent_at, const char *source_observed_at, uint64_t frame_age_ms)
{
    int64_t age;
    if (!meter_timestamp_delta_seconds(frame_sent_at, source_observed_at, &age) || age < 0) return true;
    if (frame_age_ms / 1000u >= METER_STALE_AFTER_SECONDS) return true;
    return (uint64_t)age + frame_age_ms / 1000u >= METER_STALE_AFTER_SECONDS;
}

static bool node_number(jdoc_t *doc, int node, double *number)
{
    if (node < 0 || doc->nodes[node].type != J_NUMBER) return false;
    size_t length = doc->nodes[node].raw_end - doc->nodes[node].raw_start;
    char text[64];
    if (!length || length >= sizeof(text)) return false;
    memcpy(text, doc->raw + doc->nodes[node].raw_start, length);
    text[length] = '\0';
    char *end = NULL;
    double value = strtod(text, &end);
    if (!end || *end || !isfinite(value)) return false;
    *number = value;
    return true;
}

static bool nullable_number(jdoc_t *doc, int node, double *number, bool *is_null)
{
    if (node < 0) return false;
    if (doc->nodes[node].type == J_NULL) { *is_null = true; return true; }
    *is_null = false;
    return node_number(doc, node, number) && *number >= 0;
}

static bool valid_percent(jdoc_t *doc, int node, double *number, bool *is_null)
{
    if (!nullable_number(doc, node, number, is_null)) return false;
    return *is_null || (*number >= 0 && *number <= 100);
}

static bool valid_timestamp_node(jdoc_t *doc, int node, bool nullable, int64_t *epoch, bool *is_null)
{
    const char *value = NULL;
    size_t length = 0;
    if (!nullable_string(doc, node, &value, &length)) return false;
    *is_null = value == NULL;
    if (*is_null) return nullable;
    return parse_timestamp(value, length, epoch);
}

static bool valid_nonempty_string(jdoc_t *doc, int node)
{
    size_t length;
    const char *value = string_value(doc, node, &length);
    return value && length > 0;
}

static bool valid_identity(jdoc_t *doc, int node, bool nullable)
{
    if (node < 0) return false;
    if (doc->nodes[node].type == J_NULL) return nullable;
    size_t length;
    const char *value = string_value(doc, node, &length);
    if (!value || !length || !((value[0] >= 'a' && value[0] <= 'z') || (value[0] >= '0' && value[0] <= '9'))) return false;
    for (size_t i = 0; i < length; i++) {
        char c = value[i];
        if (!((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '.' || c == '_' || c == '-')) return false;
    }
    return true;
}

static bool validate_window(jdoc_t *doc, int window)
{
    static const char *const allowed[] = {"window_id","label","used_units","remaining_units","limit_units","unit","percent_used","percent_remaining","resets_at","reset_status"};
    static const char *const required[] = {"window_id","label","used_units","remaining_units","limit_units","unit","percent_used","percent_remaining","resets_at"};
    if (!allowed_keys(doc, window, allowed, sizeof(allowed)/sizeof(allowed[0])) ||
        !all_required(doc, window, required, sizeof(required)/sizeof(required[0])) ||
        !valid_identity(doc, object_get(doc, window, "window_id"), false) ||
        !valid_nonempty_string(doc, object_get(doc, window, "label"))) return false;
    int unit = object_get(doc, window, "unit");
    bool percent = string_is(doc, unit, "percent");
    bool token = string_is(doc, unit, "token");
    bool credit = string_is(doc, unit, "credit");
    bool unknown = string_is(doc, unit, "unknown");
    if (!(percent || token || credit || unknown)) return false;
    double values[3] = {0,0,0};
    bool nulls[3];
    const char *keys[] = {"used_units","remaining_units","limit_units"};
    for (size_t i = 0; i < 3; i++) if (!nullable_number(doc, object_get(doc, window, keys[i]), &values[i], &nulls[i])) return false;
    if (percent && (!nulls[0] || !nulls[1] || !nulls[2])) return false;
    if ((token || credit) && (nulls[0] || nulls[1] || nulls[2])) return false;
    if (unknown && (!nulls[0] || !nulls[1] || !nulls[2])) return false;
    if (!nulls[0] && !nulls[1] && !nulls[2] && fabs((values[0] + values[1]) - values[2]) > 0.01) return false;
    double used_percent = 0, remaining_percent = 0;
    bool used_null, remaining_null;
    if (!valid_percent(doc, object_get(doc, window, "percent_used"), &used_percent, &used_null) ||
        !valid_percent(doc, object_get(doc, window, "percent_remaining"), &remaining_percent, &remaining_null)) return false;
    if (used_null != remaining_null) return false;
    if (!used_null && fabs((used_percent + remaining_percent) - 100.0) > 0.01) return false;
    bool reset_null;
    int64_t reset_epoch;
    if (!valid_timestamp_node(doc, object_get(doc, window, "resets_at"), true, &reset_epoch, &reset_null)) return false;
    int reset_status = object_get(doc, window, "reset_status");
    if (reset_status >= 0) {
        const char *expected = reset_null ? "unknown" : "scheduled";
        if (!reset_null) {
            int64_t ignored;
            const char *sent = string_value(doc, object_get(doc, 0, "sent_at"), NULL);
            if (sent && parse_timestamp(sent, strlen(sent), &ignored) && reset_epoch < ignored) expected = "expired";
        }
        if (!string_is(doc, reset_status, expected)) return false;
    }
    return true;
}

static bool validate_snapshot(jdoc_t *doc, int snapshot, int64_t sent_epoch)
{
    static const char *const allowed[] = {"schema_version","snapshot_id","provider_id","agent_id","host_id","model_id","account_profile_id","source_kind","metric_kind","unit","status","observed_at","windows","stale","last_good_at","error_code","error_reason"};
    static const char *const required[] = {"schema_version","snapshot_id","provider_id","agent_id","host_id","model_id","account_profile_id","source_kind","metric_kind","unit","status","observed_at","windows","stale","last_good_at","error_code","error_reason"};
    if (!allowed_keys(doc, snapshot, allowed, sizeof(allowed)/sizeof(allowed[0])) ||
        !all_required(doc, snapshot, required, sizeof(required)/sizeof(required[0]))) return false;
    double version;
    if (!node_number(doc, object_get(doc, snapshot, "schema_version"), &version) || version != 1.0 ||
        !valid_nonempty_string(doc, object_get(doc, snapshot, "snapshot_id")) ||
        !valid_identity(doc, object_get(doc, snapshot, "provider_id"), false) ||
        !valid_identity(doc, object_get(doc, snapshot, "agent_id"), true) ||
        !valid_identity(doc, object_get(doc, snapshot, "host_id"), true) ||
        !nullable_string(doc, object_get(doc, snapshot, "model_id"), NULL, NULL) ||
        !valid_identity(doc, object_get(doc, snapshot, "account_profile_id"), true)) return false;
    int source_kind = object_get(doc, snapshot, "source_kind");
    if (!(string_is(doc, source_kind, "fixture") || string_is(doc, source_kind, "local_runtime") || string_is(doc, source_kind, "provider_api") || string_is(doc, source_kind, "ide_telemetry") || string_is(doc, source_kind, "unknown"))) return false;
    int metric = object_get(doc, snapshot, "metric_kind");
    if (!(string_is(doc, metric, "quota_window") || string_is(doc, metric, "token_balance") || string_is(doc, metric, "credits") || string_is(doc, metric, "session_telemetry"))) return false;
    int unit = object_get(doc, snapshot, "unit");
    bool unit_percent = string_is(doc, unit, "percent");
    bool unit_token = string_is(doc, unit, "token");
    bool unit_credit = string_is(doc, unit, "credit");
    bool unit_unknown = string_is(doc, unit, "unknown");
    if (!(unit_percent || unit_token || unit_credit || unit_unknown)) return false;
    int status = object_get(doc, snapshot, "status");
    bool is_available = string_is(doc, status, "available");
    bool is_stale = string_is(doc, status, "stale");
    bool is_error = string_is(doc, status, "error") || string_is(doc, status, "unavailable") ||
                    string_is(doc, status, "unsupported") || string_is(doc, status, "unauthorized");
    if (!(is_available || is_stale || is_error)) return false;
    if (is_available &&
        (!valid_identity(doc, object_get(doc, snapshot, "agent_id"), false) ||
         !valid_identity(doc, object_get(doc, snapshot, "host_id"), false))) return false;
    int stale_node = object_get(doc, snapshot, "stale");
    if (stale_node < 0 || doc->nodes[stale_node].type != J_BOOL) return false;
    bool stale_value = doc->nodes[stale_node].text_length != 0;
    if ((is_available && stale_value) || (is_stale && !stale_value)) return false;
    int64_t observed_epoch = 0, last_good_epoch = 0;
    bool observed_null, last_good_null;
    if (!valid_timestamp_node(doc, object_get(doc, snapshot, "observed_at"), true, &observed_epoch, &observed_null) ||
        !valid_timestamp_node(doc, object_get(doc, snapshot, "last_good_at"), true, &last_good_epoch, &last_good_null)) return false;
    if (!observed_null && observed_epoch > sent_epoch) return false;
    if (!last_good_null && (last_good_epoch > sent_epoch || (!observed_null && last_good_epoch > observed_epoch))) return false;
    int code = object_get(doc, snapshot, "error_code");
    int reason = object_get(doc, snapshot, "error_reason");
    const char *error_text = NULL;
    if (!nullable_string(doc, code, &error_text, NULL) || !nullable_string(doc, reason, NULL, NULL)) return false;
    if ((is_error || is_stale) && (!error_text || !*error_text || !valid_nonempty_string(doc, reason))) return false;
    if (is_available && error_text) return false;
    if (is_stale && last_good_null) return false;
    if (!observed_null) {
        int64_t age = sent_epoch - observed_epoch;
        if (is_available && age >= METER_STALE_AFTER_SECONDS) return false;
        if (is_stale && age < METER_STALE_AFTER_SECONDS) return false;
    }
    int windows = object_get(doc, snapshot, "windows");
    if (windows < 0 || doc->nodes[windows].type != J_ARRAY) return false;
    for (int child = doc->nodes[windows].first; child >= 0; child = doc->nodes[child].next) {
        if (!validate_window(doc, child)) return false;
        int wid = object_get(doc, child, "window_id");
        for (int prior = doc->nodes[windows].first; prior != child; prior = doc->nodes[prior].next) {
            int previous = object_get(doc, prior, "window_id");
            size_t a_len, b_len;
            const char *a = string_value(doc, wid, &a_len);
            const char *b = string_value(doc, previous, &b_len);
            if (a_len == b_len && memcmp(a, b, a_len) == 0) return false;
        }
        int window_unit = object_get(doc, child, "unit");
        if (unit_percent && !(string_is(doc, window_unit, "percent") || string_is(doc, window_unit, "unknown"))) return false;
        if (unit_token && !(string_is(doc, window_unit, "token") || string_is(doc, window_unit, "unknown"))) return false;
    }
    return true;
}

static bool validate_global_reset(jdoc_t *doc, int reset, int64_t sent_epoch)
{
    static const char *const allowed[] = {"schema_version","source","captured_at","latest_reset_at","forecast_24h_percent","forecast_48h_percent","forecast_is_schedule","stale","error_code"};
    static const char *const required[] = {"schema_version","source","captured_at","latest_reset_at","forecast_24h_percent","forecast_48h_percent","forecast_is_schedule","stale","error_code"};
    if (!allowed_keys(doc, reset, allowed, sizeof(allowed)/sizeof(allowed[0])) ||
        !all_required(doc, reset, required, sizeof(required)/sizeof(required[0])) ||
        !valid_nonempty_string(doc, object_get(doc, reset, "source"))) return false;
    double version;
    if (!node_number(doc, object_get(doc, reset, "schema_version"), &version) || version != 1.0) return false;
    int64_t captured_epoch, latest_epoch;
    bool captured_null, latest_null;
    if (!valid_timestamp_node(doc, object_get(doc, reset, "captured_at"), false, &captured_epoch, &captured_null) ||
        captured_epoch > sent_epoch ||
        !valid_timestamp_node(doc, object_get(doc, reset, "latest_reset_at"), true, &latest_epoch, &latest_null)) return false;
    double forecast;
    bool forecast_null;
    if (!valid_percent(doc, object_get(doc, reset, "forecast_24h_percent"), &forecast, &forecast_null) ||
        !valid_percent(doc, object_get(doc, reset, "forecast_48h_percent"), &forecast, &forecast_null)) return false;
    int schedule = object_get(doc, reset, "forecast_is_schedule");
    int stale = object_get(doc, reset, "stale");
    if (schedule < 0 || doc->nodes[schedule].type != J_BOOL || doc->nodes[schedule].text_length != 0 ||
        stale < 0 || doc->nodes[stale].type != J_BOOL) return false;
    return nullable_string(doc, object_get(doc, reset, "error_code"), NULL, NULL);
}

static bool validate_frame(jdoc_t *doc, uint32_t *sequence)
{
    static const char *const frame_keys[] = {"protocol","sequence","sent_at","payload","integrity"};
    static const char *const integrity_keys[] = {"algorithm","value"};
    static const char *const payload_keys[] = {"usage","global_resets"};
    if (!allowed_keys(doc, 0, frame_keys, 5) || !all_required(doc, 0, frame_keys, 5) ||
        !string_is(doc, object_get(doc, 0, "protocol"), "cdm/1")) return false;
    int seq = object_get(doc, 0, "sequence");
    double value;
    if (!node_number(doc, seq, &value) || value < 0 || value > 4294967295.0 || floor(value) != value) return false;
    *sequence = (uint32_t)value;
    const char *sent = string_value(doc, object_get(doc, 0, "sent_at"), NULL);
    int64_t sent_epoch;
    if (!sent || !parse_timestamp(sent, strlen(sent), &sent_epoch)) return false;
    int payload = object_get(doc, 0, "payload");
    if (!allowed_keys(doc, payload, payload_keys, 2) || !all_required(doc, payload, payload_keys, 2)) return false;
    int usage = object_get(doc, payload, "usage");
    int resets = object_get(doc, payload, "global_resets");
    if (usage < 0 || doc->nodes[usage].type != J_ARRAY || resets < 0 || doc->nodes[resets].type != J_ARRAY) return false;
    for (int item = doc->nodes[usage].first; item >= 0; item = doc->nodes[item].next) {
        if (!validate_snapshot(doc, item, sent_epoch)) return false;
    }
    for (int item = doc->nodes[resets].first; item >= 0; item = doc->nodes[item].next) {
        if (!validate_global_reset(doc, item, sent_epoch)) return false;
    }
    int integrity = object_get(doc, 0, "integrity");
    if (!allowed_keys(doc, integrity, integrity_keys, 2) || !all_required(doc, integrity, integrity_keys, 2) ||
        !string_is(doc, object_get(doc, integrity, "algorithm"), "crc32")) return false;
    size_t crc_len;
    const char *crc = string_value(doc, object_get(doc, integrity, "value"), &crc_len);
    if (!crc || crc_len != 8) return false;
    for (size_t i = 0; i < crc_len; i++) if (!((crc[i] >= '0' && crc[i] <= '9') || (crc[i] >= 'A' && crc[i] <= 'F'))) return false;
    return true;
}

typedef struct { char *bytes; size_t capacity; size_t length; bool failed; } writer_t;

static void write_bytes(writer_t *w, const char *bytes, size_t length)
{
    if (w->failed || w->length + length > w->capacity) { w->failed = true; return; }
    memcpy(w->bytes + w->length, bytes, length);
    w->length += length;
}

static void write_char(writer_t *w, char c) { write_bytes(w, &c, 1); }

static void write_string(writer_t *w, const char *value, size_t length)
{
    write_char(w, '"');
    for (size_t i = 0; i < length; i++) {
        unsigned char c = (unsigned char)value[i];
        switch (c) {
        case '"': write_bytes(w, "\\\"", 2); break;
        case '\\': write_bytes(w, "\\\\", 2); break;
        case '\b': write_bytes(w, "\\b", 2); break;
        case '\f': write_bytes(w, "\\f", 2); break;
        case '\n': write_bytes(w, "\\n", 2); break;
        case '\r': write_bytes(w, "\\r", 2); break;
        case '\t': write_bytes(w, "\\t", 2); break;
        default:
            if (c < 0x20) {
                char escaped[6] = {'\\','u','0','0','0','0'};
                static const char hex[] = "0123456789abcdef";
                escaped[4] = hex[c >> 4]; escaped[5] = hex[c & 0x0f];
                write_bytes(w, escaped, sizeof(escaped));
            } else write_char(w, (char)c);
        }
    }
    write_char(w, '"');
}

static int compare_nodes(const void *left, const void *right)
{
    int a = *(const int *)left, b = *(const int *)right;
    const jnode_t *na = &sort_doc->nodes[a], *nb = &sort_doc->nodes[b];
    size_t common = na->key_length < nb->key_length ? na->key_length : nb->key_length;
    int order = memcmp(sort_doc->strings + na->key_offset,
                       sort_doc->strings + nb->key_offset, common);
    if (order) return order;
    return na->key_length < nb->key_length ? -1 : na->key_length > nb->key_length ? 1 : 0;
}

static void write_node(jdoc_t *doc, int index, writer_t *w, bool omit_integrity)
{
    jnode_t *node = &doc->nodes[index];
    switch (node->type) {
    case J_NULL: write_bytes(w, "null", 4); break;
    case J_BOOL: {
        const char *text = node->text_length ? "true" : "false";
        write_bytes(w, text, node->text_length ? 4 : 5);
        break;
    }
    case J_NUMBER:
        write_bytes(w, (const char *)doc->raw + node->raw_start, node->raw_end - node->raw_start);
        break;
    case J_STRING:
        write_string(w, doc->strings + node->text_offset, node->text_length);
        break;
    case J_ARRAY: {
        write_char(w, '[');
        bool first = true;
        for (int child = node->first; child >= 0; child = doc->nodes[child].next) {
            if (!first) write_char(w, ',');
            first = false;
            write_node(doc, child, w, false);
        }
        write_char(w, ']');
        break;
    }
    case J_OBJECT: {
        size_t count = 0;
        for (int child = node->first; child >= 0; child = doc->nodes[child].next) {
            if (!(omit_integrity && index == 0 && key_equals(doc, child, "integrity"))) count++;
        }
        int *children = count ? (int *)malloc(count * sizeof(int)) : NULL;
        if (count && !children) { w->failed = true; return; }
        size_t at = 0;
        for (int child = node->first; child >= 0; child = doc->nodes[child].next) {
            if (!(omit_integrity && index == 0 && key_equals(doc, child, "integrity"))) children[at++] = child;
        }
        sort_doc = doc;
        if (count > 1) qsort(children, count, sizeof(int), compare_nodes);
        write_char(w, '{');
        for (size_t i = 0; i < count; i++) {
            if (i) write_char(w, ',');
            jnode_t *child = &doc->nodes[children[i]];
            write_string(w, doc->strings + child->key_offset, child->key_length);
            write_char(w, ':');
            write_node(doc, children[i], w, false);
        }
        write_char(w, '}');
        free(children);
        break;
    }
    default: w->failed = true; break;
    }
}

uint32_t meter_crc32(const uint8_t *bytes, size_t length)
{
    uint32_t crc = 0xffffffffu;
    for (size_t i = 0; i < length; i++) {
        crc ^= bytes[i];
        for (int bit = 0; bit < 8; bit++) crc = (crc >> 1) ^ (0xedb88320u & (uint32_t)-(int32_t)(crc & 1u));
    }
    return crc ^ 0xffffffffu;
}

bool meter_sequence_is_newer(uint32_t candidate, uint32_t current)
{
    uint32_t distance = candidate - current;
    return distance != 0 && distance < 0x80000000u;
}

void meter_receiver_init(meter_receiver_t *receiver)
{
    if (receiver) memset(receiver, 0, sizeof(*receiver));
}

void meter_receiver_deinit(meter_receiver_t *receiver)
{
    if (!receiver) return;
    free(receiver->last_good_line);
    memset(receiver, 0, sizeof(*receiver));
}

void meter_receiver_poll(meter_receiver_t *receiver, uint64_t monotonic_ms)
{
    if (!receiver || !receiver->has_good_frame) return;
    receiver->receive_stale = monotonic_ms >= receiver->accepted_at_ms &&
        monotonic_ms - receiver->accepted_at_ms >= (uint64_t)METER_STALE_AFTER_SECONDS * 1000u;
}

static bool reject(meter_receiver_t *receiver, const char *code, jdoc_t *doc)
{
    set_error(receiver, code);
    if (doc) doc_free(doc);
    return false;
}

bool meter_receiver_receive(meter_receiver_t *receiver,
                            const uint8_t *line,
                            size_t length,
                            uint64_t monotonic_ms)
{
    if (!receiver || !line) return false;
    meter_receiver_poll(receiver, monotonic_ms);
    if (length == 0 || length > METER_MAX_FRAME_BYTES) return reject(receiver, "FRAME_SIZE_INVALID", NULL);
    if (line[length - 1] != '\n' || memchr(line, '\n', length - 1) ||
        (length >= 2 && line[length - 2] == '\r')) return reject(receiver, "FRAME_NEWLINE_INVALID", NULL);
    jdoc_t doc;
    if (!doc_parse(&doc, line, length - 1)) {
        const char *code = doc.nodes || doc.strings ? "FRAME_JSON_INVALID" : "FRAME_ALLOC_FAILED";
        return reject(receiver, code, &doc);
    }
    uint32_t sequence;
    if (!validate_frame(&doc, &sequence)) return reject(receiver, "FRAME_SCHEMA_INVALID", &doc);
    int integrity = object_get(&doc, 0, "integrity");
    int crc_node = object_get(&doc, integrity, "value");
    const char *crc_text = string_value(&doc, crc_node, NULL);
    char expected_text[9];
    writer_t unsigned_writer;
    unsigned_writer.capacity = length + 8;
    unsigned_writer.bytes = (char *)malloc(unsigned_writer.capacity);
    unsigned_writer.length = 0;
    unsigned_writer.failed = false;
    if (!unsigned_writer.bytes) return reject(receiver, "FRAME_ALLOC_FAILED", &doc);
    write_node(&doc, 0, &unsigned_writer, true);
    uint32_t expected_crc = unsigned_writer.failed ? 0 : meter_crc32((const uint8_t *)unsigned_writer.bytes, unsigned_writer.length);
    snprintf(expected_text, sizeof(expected_text), "%08" PRIX32, expected_crc);
    bool crc_ok = !unsigned_writer.failed && strlen(expected_text) == 8 && memcmp(crc_text, expected_text, 8) == 0;
    free(unsigned_writer.bytes);
    if (!crc_ok) return reject(receiver, "CRC_MISMATCH", &doc);

    writer_t canonical;
    canonical.capacity = length + 8;
    canonical.bytes = (char *)malloc(canonical.capacity);
    canonical.length = 0;
    canonical.failed = false;
    if (!canonical.bytes) return reject(receiver, "FRAME_ALLOC_FAILED", &doc);
    write_node(&doc, 0, &canonical, false);
    bool canonical_ok = !canonical.failed && canonical.length == length - 1 &&
        memcmp(canonical.bytes, line, canonical.length) == 0;
    free(canonical.bytes);
    if (!canonical_ok) return reject(receiver, "FRAME_NON_CANONICAL", &doc);
    if (receiver->has_sequence) {
        if (sequence == receiver->sequence) return reject(receiver, "DUPLICATE_SEQUENCE", &doc);
        if (!meter_sequence_is_newer(sequence, receiver->sequence)) return reject(receiver, "OUT_OF_ORDER_SEQUENCE", &doc);
    }
    char *copy = (char *)malloc(length + 1);
    if (!copy) return reject(receiver, "FRAME_ALLOC_FAILED", &doc);
    memcpy(copy, line, length);
    copy[length] = '\0';
    free(receiver->last_good_line);
    receiver->last_good_line = copy;
    receiver->last_good_length = length;
    receiver->has_good_frame = true;
    receiver->has_sequence = true;
    receiver->sequence = sequence;
    receiver->accepted_at_ms = monotonic_ms;
    receiver->receive_stale = false;
    receiver->last_error[0] = '\0';
    doc_free(&doc);
    return true;
}
