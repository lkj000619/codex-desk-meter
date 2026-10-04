#include "gui_format.h"

#include <stdio.h>
#include <string.h>

const char *gui_screen_name(int screen) {
    switch (screen) {
        case 0: return "DASHBOARD";
        case 1: return "GLOBAL RESET";
        case 2: return "STATUS";
        default: return "?";
    }
}

static const char *or_na(const char *s) {
    return (s && *s) ? s : "n/a";
}

void gui_dashboard_line(const char *provider, const char *window,
                        const char *percent_remaining, const char *unit,
                        char *out, size_t out_sz) {
    char pct[32];
    if (percent_remaining && *percent_remaining) {
        snprintf(pct, sizeof pct, "REM %s%%", percent_remaining);
    } else {
        snprintf(pct, sizeof pct, "n/a");
    }
    snprintf(out, out_sz, "%s/%s %s %s", or_na(provider), or_na(window), pct,
             or_na(unit));
    out[out_sz - 1] = '\0';
}

void gui_dashboard_time_line(const char *resets_at, const char *observed_at,
                             char *out, size_t out_sz) {
    snprintf(out, out_sz, "R:%s O:%s", or_na(resets_at), or_na(observed_at));
    out[out_sz - 1] = '\0';
}

void gui_global_text(const char *source, const char *latest_reset_at,
                     const char *captured_at, const char *age_text, int has_reset,
                     gui_screen_text_t *out) {
    memset(out, 0, sizeof *out);
    if (!has_reset) {
        snprintf(out->lines[0], sizeof out->lines[0], "GLOBAL RESET: default (no history)");
        snprintf(out->lines[1], sizeof out->lines[1], "src:%s", or_na(source));
        snprintf(out->lines[2], sizeof out->lines[2], "obs:%s", or_na(captured_at));
        out->count = 3;
        return;
    }
    snprintf(out->lines[0], sizeof out->lines[0], "GLOBAL RESET src:%s", or_na(source));
    snprintf(out->lines[1], sizeof out->lines[1], "latest:%s", or_na(latest_reset_at));
    snprintf(out->lines[2], sizeof out->lines[2], "age:%s obs:%s", or_na(age_text), or_na(captured_at));
    out->count = 3;
}

void gui_status_text(int link_ok, const char *last_error, int stale,
                     const char *last_good_at, const char *retry,
                     gui_screen_text_t *out) {
    memset(out, 0, sizeof *out);
    snprintf(out->lines[0], sizeof out->lines[0], "LINK:%s STALE:%s", link_ok ? "USB-OK" : "USB-LOST",
             stale ? "YES" : "NO");
    snprintf(out->lines[1], sizeof out->lines[1], "ERR:%s", or_na(last_error));
    snprintf(out->lines[2], sizeof out->lines[2], "LAST-GOOD:%s", or_na(last_good_at));
    snprintf(out->lines[3], sizeof out->lines[3], "RETRY:%s", or_na(retry));
    out->count = 4;
}

int gui_layout_fits(const gui_screen_text_t *screen) {
    if (!screen || screen->count < 0 || screen->count > GUI_LINES_MAX) {
        return 0;
    }
    for (int i = 0; i < screen->count; i++) {
        if (strlen(screen->lines[i]) > GUI_LINE_CHARS) {
            return 0;
        }
    }
    return 1;
}
