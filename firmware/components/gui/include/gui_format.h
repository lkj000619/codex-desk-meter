#pragma once
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

#define GUI_LINES_MAX 12
#define GUI_LINE_CHARS 64
#define GUI_SCREENS 3 /* 0 dashboard, 1 global reset, 2 status/error */

/* Logical landscape canvas: 820x320. Text uses a 8x16 cell font so the
 * safe grid is 820/8=102 cols x 320/16=20 rows; lines are capped at 64
 * chars so nothing clips on the real panel. */
typedef struct {
    char lines[GUI_LINES_MAX][GUI_LINE_CHARS + 1];
    int count;
} gui_screen_text_t;

/* Render one dashboard window as two 64-char rows: a summary row and a
 * provenance row. All strings are verbatim from the frame payload (never
 * invented). Missing values render as "n/a". */
void gui_dashboard_line(const char *provider, const char *window,
                        const char *percent_used, const char *unit,
                        char *out, size_t out_sz);
void gui_dashboard_time_line(const char *resets_at, const char *observed_at,
                             char *out, size_t out_sz);

/* Global reset screen. Shows codex-resets.com latest reset + age text
 * supplied by the caller (firmware passes receive-age; "unknown" when the
 * wall-clock base is not established), or the default screen. */
void gui_global_text(const char *source, const char *latest_reset_at,
                     const char *captured_at, const char *age_text, int has_reset,
                     gui_screen_text_t *out);

/* Status screen: link / parse-error / stale / last-good / retry state. */
void gui_status_text(int link_ok, const char *last_error, int stale,
                     const char *last_good_at, const char *retry,
                     gui_screen_text_t *out);

/* Returns 1 when every line fits the 64-char landscape budget. */
int gui_layout_fits(const gui_screen_text_t *screen);

const char *gui_screen_name(int screen);

#ifdef __cplusplus
}
#endif
