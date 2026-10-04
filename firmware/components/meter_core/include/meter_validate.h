#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Pure numeric/semantic rules shared by firmware GUI and host tests.
 * All functions are dependency-free so they compile on ESP32 and the host. */

/* Percent pair must both be null or both set; when set they sum to 100 ± 0.01. */
int meter_percent_pair_ok(int used_null, double used, int rem_null, double rem);

/* Absolute token/credit windows: used+remaining == limit within 0.01. All set. */
int meter_absolute_ok(double used, double remaining, double limit);

/* Classify a window/global reset timestamp against a UTC reference.
 * resets_at may be NULL/empty -> "unknown". Returns "scheduled", "expired",
 * or "unknown" via out (NUL-terminated). strcmp-based: valid for fixed UTC. */
void meter_reset_classify(const char *resets_at, const char *reference_time,
                          char *out, unsigned out_sz);

/* Source age staleness: observed_at vs reference_time, threshold 300 s.
 * Inputs are "YYYY-MM-DDTHH:MM:SSZ" UTC. Returns 1 when age >= 300 s,
 * 0 when fresh, -1 when the timestamps are unusable (caller keeps unknown). */
int meter_source_age_stale(const char *observed_at, const char *reference_time);

#ifdef __cplusplus
}
#endif
