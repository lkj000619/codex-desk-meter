/* Host test for production GUI text (gui_format.c): provenance strings are
 * preserved verbatim, default screens exist, and every line fits the
 * 820 px landscape budget (64 chars). */
#include <stdio.h>
#include <string.h>

#include "gui_format.h"

static int failures;

#define CHECK(cond)                                                            \
    do {                                                                       \
        if (!(cond)) {                                                         \
            printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond);              \
            failures++;                                                        \
        }                                                                      \
    } while (0)

int main(void) {
    char line[65], tline[65];
    gui_dashboard_line("openai", "five-hour", "20", "percent", line, sizeof line);
    gui_dashboard_time_line("2026-09-10T05:00:00Z", "2026-09-10T00:00:00Z",
                            tline, sizeof tline);
    CHECK(strstr(line, "openai") != NULL);
    CHECK(strstr(line, "five-hour") != NULL);
    CHECK(strstr(line, "20%") != NULL);
    CHECK(strstr(line, "REM") != NULL);
    CHECK(strstr(tline, "2026-09-10T05:00:00Z") != NULL);
    CHECK(strstr(tline, "2026-09-10T00:00:00Z") != NULL);
    CHECK(strlen(line) <= 64);
    CHECK(strlen(tline) <= 64);

    /* Legacy fixture values render as remaining percentages. */
    gui_dashboard_line("fixture", "five-hour", "58", "percent", line, sizeof line);
    CHECK(strstr(line, "58%") != NULL);
    CHECK(strstr(line, "REM") != NULL);
    gui_dashboard_line("fixture", "weekly", "82", "percent", line, sizeof line);
    CHECK(strstr(line, "82%") != NULL);
    CHECK(strlen(line) <= 64);

    /* Nulls render as n/a, never as invented values. */
    gui_dashboard_line(NULL, NULL, NULL, NULL, line, sizeof line);
    CHECK(strstr(line, "n/a") != NULL);

    gui_screen_text_t g;
    gui_global_text("codex-resets.com", "2026-09-08T01:56:00Z",
                    "2026-09-10T16:54:07Z", "172081s (rx-age)", 1, &g);
    CHECK(g.count == 3);
    CHECK(strstr(g.lines[0], "codex-resets.com") != NULL);
    CHECK(strstr(g.lines[1], "2026-09-08T01:56:00Z") != NULL);
    CHECK(gui_layout_fits(&g) == 1);

    gui_global_text("codex-resets.com", NULL, NULL, NULL, 0, &g);
    CHECK(strstr(g.lines[0], "default") != NULL);
    CHECK(gui_layout_fits(&g) == 1);

    gui_screen_text_t s;
    gui_status_text(0, "CRC_MISMATCH", 1, "2026-09-10T00:04:59Z", "reopen<=1Hz", &s);
    CHECK(s.count == 4);
    CHECK(strstr(s.lines[0], "USB-LOST") != NULL);
    CHECK(strstr(s.lines[1], "CRC_MISMATCH") != NULL);
    CHECK(gui_layout_fits(&s) == 1);

    /* Long provenance still fits: truncation is by construction (64 cap). */
    char long_line[65];
    memset(long_line, 'x', 64);
    long_line[64] = '\0';
    gui_screen_text_t t;
    memcpy(t.lines[0], long_line, 65);
    t.count = 1;
    CHECK(gui_layout_fits(&t) == 1);
    t.lines[0][64] = 'y'; /* 65 chars must fail */
    CHECK(gui_layout_fits(&t) == 0);

    if (failures == 0) {
        printf("test_gui_regression: PASS\n");
        return 0;
    }
    printf("test_gui_regression: %d FAILURES\n", failures);
    return 1;
}
