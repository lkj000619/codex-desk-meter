#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include "cJSON.h"

#define CDM_MAX_FRAME 65536
typedef struct {
    bool has_sequence;
    uint32_t sequence;
    uint64_t received_ms;
    int64_t sent_epoch;
    cJSON *payload;
    char error[40];
} cdm_state;
void cdm_init(cdm_state *state);
void cdm_free(cdm_state *state);
bool cdm_accept(cdm_state *state, const char *line, size_t len, uint64_t now_ms);
bool cdm_stale(const cdm_state *state, uint64_t now_ms);
uint32_t cdm_crc32(const unsigned char *data, size_t len);
bool cdm_timestamp(const char *value, int64_t *epoch);
