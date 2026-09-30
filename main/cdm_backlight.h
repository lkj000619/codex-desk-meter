#ifndef CDM_BACKLIGHT_H
#define CDM_BACKLIGHT_H

#include <stdint.h>

// The Waveshare board drives its backlight through an active-low LEDC input.
static inline uint32_t cdm_backlight_duty(uint8_t brightness_percent) {
    if (brightness_percent > 100) brightness_percent = 100;
    return 255u - ((255u * brightness_percent + 50u) / 100u);
}

#endif
