#include "feature.h"
#include "board.h"
void feature_idle_dimming(uint64_t now_ms,uint64_t last_frame_ms,bool has_frame) {
    // Optional power feature: retain a readable display and brighten immediately on data.
    static bool dimmed=false;
    bool idle=has_frame && now_ms-last_frame_ms>=60000;
    if(idle!=dimmed) { board_brightness(idle?100:200); dimmed=idle; }
}
