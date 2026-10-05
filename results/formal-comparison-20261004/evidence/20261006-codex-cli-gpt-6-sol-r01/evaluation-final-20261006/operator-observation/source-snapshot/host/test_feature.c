#include "feature.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
static int brightness=-1;
void board_brightness(uint8_t value) { brightness=value; }
int main(void) {
    feature_idle_dimming(100000,40001,true); assert(brightness==-1);
    feature_idle_dimming(100001,40001,true); assert(brightness==100);
    feature_idle_dimming(100002,100002,true); assert(brightness==200);
    puts("idle backlight boundary and restore: PASS"); return 0;
}
