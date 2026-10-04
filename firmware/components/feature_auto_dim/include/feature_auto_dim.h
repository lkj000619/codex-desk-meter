#pragma once
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Selected onboard feature: link/idle-aware backlight auto-dim.
 * Separate from the core meter path; core rendering never depends on it.
 * Backlight is active-low (GPIO6): duty = 255 - brightness. */

#define AUTODIM_BRIGHT_NORMAL 200u
#define AUTODIM_BRIGHT_DIM 60u
#define AUTODIM_IDLE_SECONDS 30u

typedef struct {
    uint64_t last_activity_s; /* last accepted frame or BOOT press */
    int link_ok;
} autodim_state_t;

void autodim_init(autodim_state_t *s, uint64_t now_s);

/* Returns the 8-bit LEDC duty for the current conditions. Pure logic. */
uint8_t autodim_duty(const autodim_state_t *s, uint64_t now_s);

/* 1 when the panel is in dimmed standby, else 0. */
int autodim_is_dimmed(const autodim_state_t *s, uint64_t now_s);

#ifdef __cplusplus
}
#endif
