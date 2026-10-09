#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include "cJSON.h"

#define CDM_MAX_FRAME 65536u

typedef struct {
    char *key;
    cJSON *current;
    cJSON *good;
    uint64_t received_ms;
} cdm_entry;

typedef struct {
    cdm_entry *usage;
    size_t usage_count;
    cdm_entry *global;
    size_t global_count;
    bool has_sequence;
    uint32_t sequence;
    bool has_frame;
    uint64_t received_ms;
    bool has_anchor;
    int64_t anchor_utc_us;
    uint64_t anchor_mono_ms;
    char wire_error[32];
} cdm_state;

void cdm_init(cdm_state *state);
void cdm_free(cdm_state *state);
bool cdm_accept(cdm_state *state, const unsigned char *line, size_t length, uint64_t mono_ms);
bool cdm_newer(uint32_t current, uint32_t candidate);
bool cdm_parse_time(const char *value, int64_t *utc_us);
bool cdm_source_age(const cdm_state *state, const cJSON *record, uint64_t mono_ms, uint64_t *age_s);
bool cdm_receive_age(const cdm_state *state, uint64_t mono_ms, uint64_t *age_s);
bool cdm_stale(const cdm_state *state, const cJSON *record, uint64_t mono_ms);
uint32_t cdm_crc32(const unsigned char *bytes, size_t length);

