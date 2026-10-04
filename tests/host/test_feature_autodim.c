/* Host test for the selected feature module (feature_auto_dim.c). */
#include <stdio.h>

#include "feature_auto_dim.h"

static int failures;

#define CHECK(cond)                                                            \
    do {                                                                       \
        if (!(cond)) {                                                         \
            printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond);              \
            failures++;                                                        \
        }                                                                      \
    } while (0)

int main(void) {
    autodim_state_t s;
    autodim_init(&s, 1000);
    /* Fresh + linked: normal brightness (active-low duty 255-200=55). */
    CHECK(autodim_is_dimmed(&s, 1000) == 0);
    CHECK(autodim_duty(&s, 1000) == (255u - 200u));
    /* Idle 29 s: still normal; 30 s: dimmed. */
    CHECK(autodim_is_dimmed(&s, 1000 + 29) == 0);
    CHECK(autodim_is_dimmed(&s, 1000 + 30) == 1);
    CHECK(autodim_duty(&s, 1000 + 30) == (255u - 60u));
    /* Link loss dims immediately even without idle. */
    s.link_ok = 0;
    CHECK(autodim_is_dimmed(&s, 1000) == 1);
    /* Activity restores normal once the link returns. */
    s.link_ok = 1;
    s.last_activity_s = 2000;
    CHECK(autodim_is_dimmed(&s, 2000) == 0);

    if (failures == 0) {
        printf("test_feature_autodim: PASS\n");
        return 0;
    }
    printf("test_feature_autodim: %d FAILURES\n", failures);
    return 1;
}
