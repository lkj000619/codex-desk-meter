/* Host test for the production BOOT debounce helper (bsp_input.c). */
#include <stdio.h>

#include "bsp_input.h"

static int failures;

#define CHECK(cond)                                                            \
    do {                                                                       \
        if (!(cond)) {                                                         \
            printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond);              \
            failures++;                                                        \
        }                                                                      \
    } while (0)

int main(void) {
    uint64_t since = 0;
    int pressed = 0;
    /* Bounce: short transitions under 50 ms never commit. */
    CHECK(bsp_input_debounce_step(1, 0, &since, &pressed) == 0);
    CHECK(bsp_input_debounce_step(0, 10, &since, &pressed) == 0);
    CHECK(pressed == 0);
    /* Stable press commits after 50 ms. */
    CHECK(bsp_input_debounce_step(1, 100, &since, &pressed) == 0);
    CHECK(bsp_input_debounce_step(1, 150, &since, &pressed) == 1);
    CHECK(pressed == 1);
    /* Stable release commits after 50 ms. */
    CHECK(bsp_input_debounce_step(0, 200, &since, &pressed) == 0);
    CHECK(bsp_input_debounce_step(0, 250, &since, &pressed) == 1);
    CHECK(pressed == 0);

    if (failures == 0) {
        printf("test_input_debounce: PASS\n");
        return 0;
    }
    printf("test_input_debounce: %d FAILURES\n", failures);
    return 1;
}
