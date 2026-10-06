#include "idle_dim_policy.h"

uint8_t idle_dim_brightness(uint64_t now_ms, uint64_t last_interaction_ms, bool display_active)
{
    if (!display_active || now_ms < last_interaction_ms) return 0;
    return now_ms - last_interaction_ms >= 60000u ? 22u : 180u;
}
