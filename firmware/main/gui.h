#pragma once
#include <stdbool.h>
#include <stdint.h>
#include "cdm.h"

typedef struct {
    unsigned screen;
    size_t quota_page;
    bool connected;
} gui_control;

void gui_render(const cdm_state *state, const gui_control *control, uint64_t mono_ms, bool temperature_known, float temperature_c);
size_t gui_quota_count(const cdm_state *state);
void gui_next_window_page(gui_control *control, const cdm_state *state);
