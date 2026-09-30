#include "cdm_backlight.h"

#include <assert.h>

int main(void) {
    assert(cdm_backlight_duty(0) == 255);
    assert(cdm_backlight_duty(50) == 127);
    assert(cdm_backlight_duty(100) == 0);
    assert(cdm_backlight_duty(255) == 0);
    return 0;
}
