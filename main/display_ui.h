#ifndef DISPLAY_UI_H
#define DISPLAY_UI_H

#include "meter_model.h"
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

esp_err_t display_ui_init(void);
void display_ui_set_screen(uint32_t screen_idx);
uint32_t display_ui_get_screen(void);
void display_ui_cycle_screen(void);
void display_ui_render(const meter_state_t *state);

#ifdef __cplusplus
}
#endif

#endif /* DISPLAY_UI_H */
