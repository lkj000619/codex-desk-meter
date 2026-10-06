#include "idle_dim_policy.h"

#include <assert.h>

int main(void)
{
    assert(idle_dim_brightness(0, 0, true) == 180);
    assert(idle_dim_brightness(59999, 0, true) == 180);
    assert(idle_dim_brightness(60000, 0, true) == 120);
    assert(idle_dim_brightness(70000, 0, false) == 0);
    assert(idle_dim_brightness(10, 20, true) == 0);
    return 0;
}
