#include "idle_dim_policy.h"

uint8_t idle_dim_brightness(uint64_t now_ms, uint64_t last_interaction_ms, bool display_active)
{
    if (!display_active || now_ms < last_interaction_ms) return 0;
    /* Keep the panel visibly illuminated during idle; 22/255 was nearly black. */
    return now_ms - last_interaction_ms >= 60000u ? 120u : 180u;
}
