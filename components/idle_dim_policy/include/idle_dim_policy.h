#ifndef IDLE_DIM_POLICY_H
#define IDLE_DIM_POLICY_H

#include <stdbool.h>
#include <stdint.h>

/* Optional power-saving feature policy; independent of the receiver/parser core. */
uint8_t idle_dim_brightness(uint64_t now_ms,
                            uint64_t last_interaction_ms,
                            bool display_active);

#endif
