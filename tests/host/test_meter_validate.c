/* Host test for production semantic rules (meter_validate.c). */
#include <stdio.h>
#include <string.h>

#include "meter_validate.h"

static int failures;

#define CHECK(cond)                                                            \
    do {                                                                       \
        if (!(cond)) {                                                         \
            printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond);              \
            failures++;                                                        \
        }                                                                      \
    } while (0)

int main(void) {
    /* Percent pairs. */
    CHECK(meter_percent_pair_ok(1, 0, 1, 0) == 1);       /* both null */
    CHECK(meter_percent_pair_ok(0, 20, 0, 80) == 1);
    CHECK(meter_percent_pair_ok(0, 20, 1, 0) == 0);       /* half null */
    CHECK(meter_percent_pair_ok(0, 20, 0, 70) == 0);       /* sum != 100 */
    CHECK(meter_percent_pair_ok(0, 101, 0, -1) == 0);      /* range */

    /* Absolute balance within 0.01. */
    CHECK(meter_absolute_ok(250, 750, 1000) == 1);
    CHECK(meter_absolute_ok(250, 750, 1000.009) == 1);
    CHECK(meter_absolute_ok(250, 750, 1001) == 0);

    /* Reset classification. */
    char cls[16];
    meter_reset_classify(NULL, "2026-09-10T00:04:59Z", cls, sizeof cls);
    CHECK(strcmp(cls, "unknown") == 0);
    meter_reset_classify("2026-09-10T05:00:00Z", "2026-09-10T00:04:59Z", cls, sizeof cls);
    CHECK(strcmp(cls, "scheduled") == 0);
    meter_reset_classify("2026-09-08T01:56:00Z", "2026-09-10T00:04:59Z", cls, sizeof cls);
    CHECK(strcmp(cls, "expired") == 0);

    /* Source-age staleness at the 300 s boundary (UTC). */
    CHECK(meter_source_age_stale("2026-09-10T00:00:00Z", "2026-09-10T00:00:00Z") == 0);
    CHECK(meter_source_age_stale("2026-09-10T00:00:00Z", "2026-09-10T00:04:59Z") == 0);
    CHECK(meter_source_age_stale("2026-09-10T00:00:00Z", "2026-09-10T00:05:00Z") == 1);
    CHECK(meter_source_age_stale("2026-09-10T00:05:01Z", "2026-09-10T00:05:00Z") == -1);
    CHECK(meter_source_age_stale("bogus", "2026-09-10T00:05:00Z") == -1);

    if (failures == 0) {
        printf("test_meter_validate: PASS\n");
        return 0;
    }
    printf("test_meter_validate: %d FAILURES\n", failures);
    return 1;
}
