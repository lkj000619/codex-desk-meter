#pragma once
#include "cJSON.h"

// Section 5 stdin seam; deliberately separate from the cdm/1 wire model.
cJSON *cdm_legacy_run(const cJSON *request);
