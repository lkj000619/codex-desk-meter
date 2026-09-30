#ifndef CDM_RTC_H
#define CDM_RTC_H

#include <stdbool.h>
#include <stdint.h>

bool cdm_rtc_init(int64_t *epoch_out);
bool cdm_rtc_sync(int64_t epoch);
bool cdm_rtc_read(int64_t *epoch_out);

#endif
