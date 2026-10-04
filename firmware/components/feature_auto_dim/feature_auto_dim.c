#include "feature_auto_dim.h"

void autodim_init(autodim_state_t *s, uint64_t now_s) {
    s->last_activity_s = now_s;
    s->link_ok = 1;
}

static int idle(const autodim_state_t *s, uint64_t now_s) {
    uint64_t age = now_s >= s->last_activity_s ? now_s - s->last_activity_s : 0;
    return age >= AUTODIM_IDLE_SECONDS;
}

int autodim_is_dimmed(const autodim_state_t *s, uint64_t now_s) {
    if (!s->link_ok) {
        return 1;
    }
    return idle(s, now_s);
}

uint8_t autodim_duty(const autodim_state_t *s, uint64_t now_s) {
    uint8_t bright = autodim_is_dimmed(s, now_s) ? AUTODIM_BRIGHT_DIM : AUTODIM_BRIGHT_NORMAL;
    return (uint8_t)(255u - bright);
}
