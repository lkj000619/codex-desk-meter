#ifndef CDM_RECEIVER_H
#define CDM_RECEIVER_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define CDM_MAX_USAGE 16
#define CDM_MAX_WINDOWS 8
#define CDM_MAX_GLOBAL_RESETS 4

typedef struct {
    char window_id[40];
    char label[48];
    char unit[12];
    double percent_used;
    double percent_remaining;
    bool has_percent_used;
    bool has_percent_remaining;
    char resets_at[32];
    char reset_status[12];
} CdmWindow;

typedef struct {
    char provider_id[32];
    char agent_id[32];
    char host_id[32];
    char status[20];
    char observed_at[32];
    char error_code[40];
    char error_reason[96];
    bool stale;
    int64_t last_good_epoch;
    size_t window_count;
    CdmWindow windows[CDM_MAX_WINDOWS];
} CdmUsage;

typedef struct {
    char source[40];
    char captured_at[32];
    char latest_reset_at[32];
    char error_code[40];
    bool stale;
    bool has_latest_reset;
    int64_t captured_epoch;
} CdmGlobalReset;

typedef enum {
    CDM_ACCEPTED = 0,
    CDM_REJECT_JSON,
    CDM_REJECT_CANONICAL,
    CDM_REJECT_SCHEMA,
    CDM_REJECT_CRC,
    CDM_REJECT_VERSION,
    CDM_REJECT_SEQUENCE,
    CDM_REJECT_CAPACITY
} CdmResult;

typedef enum {
    CDM_SCREEN_DASHBOARD = 0,
    CDM_SCREEN_GLOBAL_RESET = 1,
    CDM_SCREEN_STATUS = 2
} CdmScreen;

typedef struct {
    bool stable_pressed;
    bool candidate_pressed;
    uint32_t candidate_since_ms;
    bool initialized;
} CdmButtonDebouncer;

typedef struct {
    int year;
    int month;
    int day;
    int hour;
    int minute;
    int second;
} CdmCalendar;

typedef struct {
    bool has_good_frame;
    bool stale;
    bool has_sequence;
    uint32_t sequence;
    int64_t last_good_epoch;
    size_t usage_count;
    size_t reset_count;
    CdmUsage usage[CDM_MAX_USAGE];
    CdmGlobalReset global_resets[CDM_MAX_GLOBAL_RESETS];
    CdmResult last_error;
} CdmReceiver;

void cdm_receiver_init(CdmReceiver *receiver);
CdmResult cdm_receiver_apply(CdmReceiver *receiver, const char *json, size_t length, int64_t now_epoch);
void cdm_receiver_update_stale(CdmReceiver *receiver, int64_t now_epoch);
bool cdm_sequence_is_newer(uint32_t candidate, uint32_t current);
uint32_t cdm_crc32(const unsigned char *data, size_t length);
bool cdm_parse_epoch(const char *rfc3339, int64_t *epoch_out);
bool cdm_epoch_to_utc(int64_t epoch, CdmCalendar *calendar_out);
bool cdm_bcd_to_decimal(uint8_t bcd, uint8_t max_value, uint8_t *value_out);
CdmScreen cdm_screen_next(CdmScreen current);
bool cdm_button_update(CdmButtonDebouncer *button, bool raw_pressed, uint32_t now_ms, uint32_t debounce_ms);
size_t cdm_dashboard_page(size_t total_windows, uint64_t elapsed_seconds);

#endif
