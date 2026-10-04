#include "meter_validate.h"

#include <math.h>
#include <stdio.h>
#include <string.h>

int meter_percent_pair_ok(int used_null, double used, int rem_null, double rem) {
    if (used_null && rem_null) {
        return 1;
    }
    if (used_null != rem_null) {
        return 0;
    }
    if (used < 0 || used > 100 || rem < 0 || rem > 100) {
        return 0;
    }
    return fabs((used + rem) - 100.0) <= 0.01;
}

int meter_absolute_ok(double used, double remaining, double limit) {
    if (used < 0 || remaining < 0 || limit < 0) {
        return 0;
    }
    return fabs((used + remaining) - limit) <= 0.01;
}

void meter_reset_classify(const char *resets_at, const char *reference_time,
                          char *out, unsigned out_sz) {
    const char *unknown = "unknown";
    if (out_sz == 0) {
        return;
    }
    if (!resets_at || !*resets_at) {
        snprintf(out, out_sz, "%s", unknown);
        return;
    }
    if (!reference_time || !*reference_time) {
        snprintf(out, out_sz, "%s", unknown);
        return;
    }
    snprintf(out, out_sz, "%s", strcmp(resets_at, reference_time) >= 0 ? "scheduled" : "expired");
}

static int parse_utc(const char *s, int *y, int *mo, int *d, int *h, int *mi, int *sec) {
    if (!s || strlen(s) < 20) {
        return 0;
    }
    /* Strict "YYYY-MM-DDTHH:MM:SSZ". */
    if (s[4] != '-' || s[7] != '-' || s[10] != 'T' || s[13] != ':' || s[16] != ':' ||
        s[19] != 'Z' || s[20] != '\0') {
        return 0;
    }
    *y = (s[0] - '0') * 1000 + (s[1] - '0') * 100 + (s[2] - '0') * 10 + (s[3] - '0');
    *mo = (s[5] - '0') * 10 + (s[6] - '0');
    *d = (s[8] - '0') * 10 + (s[9] - '0');
    *h = (s[11] - '0') * 10 + (s[12] - '0');
    *mi = (s[14] - '0') * 10 + (s[15] - '0');
    *sec = (s[17] - '0') * 10 + (s[18] - '0');
    if (*mo < 1 || *mo > 12 || *d < 1 || *d > 31 || *h > 23 || *mi > 59 || *sec > 60) {
        return 0;
    }
    return 1;
}

static long long days_from_civil(int y, int m, int d) {
    y -= m <= 2;
    const long long era = (y >= 0 ? y : y - 399) / 400;
    const unsigned yoe = (unsigned)(y - era * 400);
    const unsigned doy = (153 * (m + (m > 2 ? -3 : 9)) + 2) / 5 + (unsigned)(d - 1);
    const unsigned doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
    return era * 146097 + (long long)doe - 719468;
}

int meter_source_age_stale(const char *observed_at, const char *reference_time) {
    int y1, mo1, d1, h1, mi1, s1, y2, mo2, d2, h2, mi2, s2;
    if (!parse_utc(observed_at, &y1, &mo1, &d1, &h1, &mi1, &s1)) {
        return -1;
    }
    if (!parse_utc(reference_time, &y2, &mo2, &d2, &h2, &mi2, &s2)) {
        return -1;
    }
    long long t1 = days_from_civil(y1, mo1, d1) * 86400LL + h1 * 3600LL + mi1 * 60LL + s1;
    long long t2 = days_from_civil(y2, mo2, d2) * 86400LL + h2 * 3600LL + mi2 * 60LL + s2;
    long long age = t2 - t1;
    if (age < 0) {
        return -1; /* future observed_at: caller reports FUTURE_TIMESTAMP */
    }
    return age >= 300 ? 1 : 0;
}
