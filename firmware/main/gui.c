#include "gui.h"
#include "bsp.h"
#include <string.h>

size_t gui_quota_count(const cdm_state *state)
{
    size_t count=0;
    for(size_t i=0;i<state->usage_count;i++) {
        const cJSON *record=state->usage[i].current;
        if (!record) record=state->usage[i].good;
        const cJSON *kind=cJSON_GetObjectItemCaseSensitive(record,"metric_kind");
        if (!cJSON_IsString(kind) || strcmp(kind->valuestring,"quota_window")) continue;
        const cJSON *windows=cJSON_GetObjectItemCaseSensitive(record,"windows");
        if ((!cJSON_IsArray(windows) || !windows->child) && state->usage[i].good)
            windows=cJSON_GetObjectItemCaseSensitive(state->usage[i].good,"windows");
        if (cJSON_IsArray(windows)) count+=cJSON_GetArraySize(windows);
    }
    return count;
}
void gui_next_window_page(gui_control *control,const cdm_state *state)
{
    size_t pages=(gui_quota_count(state)+1)/2;
    control->quota_page=pages?(control->quota_page+1)%pages:0;
}
void gui_render(const cdm_state *state,const gui_control *control,uint64_t mono_ms,bool temperature_known,float temperature_c)
{
    (void)state; (void)control; (void)mono_ms; (void)temperature_known; (void)temperature_c;
    // Core-build placeholder; selected B rendering waits for independent design PASS.
    bsp_fill(0,0,820,320,0xF7BE);
}
