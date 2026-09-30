#ifndef CDM_DISPLAY_H
#define CDM_DISPLAY_H

#include <stdbool.h>
#include <stdint.h>

#include "cdm_receiver.h"

bool cdm_display_init(void);
void cdm_display_render(const CdmReceiver *receiver, CdmScreen screen, int64_t now_epoch, bool rtc_ready);

#endif
