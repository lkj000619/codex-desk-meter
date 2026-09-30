#include <assert.h>
#include <stdio.h>
#include <string.h>

#include "cdm_receiver.h"

static const char *empty_frame =
    "{\"integrity\":{\"algorithm\":\"crc32\",\"value\":\"BE8028D7\"},"
    "\"payload\":{\"global_resets\":[],\"usage\":[]},"
    "\"protocol\":\"cdm/1\",\"sent_at\":\"2026-09-10T00:00:00Z\",\"sequence\":1}";

static const char *usage_frame =
    "{\"integrity\":{\"algorithm\":\"crc32\",\"value\":\"0486EA68\"},"
    "\"payload\":{\"global_resets\":[{\"captured_at\":\"2026-09-10T00:00:00Z\",\"error_code\":null,"
    "\"forecast_24h_percent\":null,\"forecast_48h_percent\":null,\"forecast_is_schedule\":false,"
    "\"latest_reset_at\":\"2026-09-08T01:56:00Z\",\"schema_version\":1,\"source\":\"codex-resets.com\",\"stale\":false}],"
    "\"usage\":[{\"account_profile_id\":null,\"agent_id\":\"codex-cli\",\"error_code\":null,"
    "\"error_reason\":null,\"host_id\":\"terminal\",\"last_good_at\":\"2026-09-10T00:00:00Z\","
    "\"metric_kind\":\"quota_window\",\"model_id\":null,\"observed_at\":\"2026-09-10T00:00:00Z\","
    "\"provider_id\":\"openai\",\"schema_version\":1,\"snapshot_id\":\"fixture-codemeter-test\","
    "\"source_kind\":\"fixture\",\"stale\":false,\"status\":\"available\",\"unit\":\"percent\","
    "\"windows\":[{\"label\":\"5h\",\"limit_units\":null,\"percent_remaining\":58,\"percent_used\":42,"
    "\"remaining_units\":null,\"reset_status\":\"unknown\",\"resets_at\":null,\"unit\":\"percent\","
    "\"used_units\":null,\"window_id\":\"five-hour\"}]}]},\"protocol\":\"cdm/1\","
    "\"sent_at\":\"2026-09-10T00:00:00Z\",\"sequence\":2}";

int main(void) {
    CdmReceiver receiver;
    cdm_receiver_init(&receiver);

    assert(cdm_crc32((const unsigned char *)"123456789", 9) == 0xCBF43926u);
    assert(cdm_sequence_is_newer(8u, 7u));
    assert(!cdm_sequence_is_newer(7u, 7u));
    assert(!cdm_sequence_is_newer(1u, 8u));
    assert(cdm_sequence_is_newer(0u, 0xFFFFFFFFu));
    assert(!cdm_sequence_is_newer(0x80000000u, 0u));
    assert(cdm_screen_next(CDM_SCREEN_DASHBOARD) == CDM_SCREEN_GLOBAL_RESET);
    assert(cdm_screen_next(CDM_SCREEN_STATUS) == CDM_SCREEN_DASHBOARD);
    assert(cdm_dashboard_page(0, 0) == 0);
    assert(cdm_dashboard_page(8, 7) == 0);
    assert(cdm_dashboard_page(9, 8) == 1);
    assert(cdm_dashboard_page(20, 24) == 0);
    CdmButtonDebouncer button = {0};
    assert(!cdm_button_update(&button, true, 100, 50));
    assert(!cdm_button_update(&button, true, 149, 50));
    assert(cdm_button_update(&button, true, 150, 50));
    assert(!cdm_button_update(&button, true, 151, 50));
    assert(!cdm_button_update(&button, false, 200, 50));
    assert(cdm_button_update(&button, false, 250, 50));
    CdmCalendar calendar;
    assert(cdm_epoch_to_utc(0, &calendar));
    assert(calendar.year == 1970 && calendar.month == 1 && calendar.day == 1);
    assert(calendar.hour == 0 && calendar.minute == 0 && calendar.second == 0);
    assert(cdm_epoch_to_utc(1799539200, &calendar));
    assert(calendar.year == 2027 && calendar.month == 1 && calendar.day == 10);
    uint8_t bcd_value = 0;
    assert(cdm_bcd_to_decimal(0x59, 59, &bcd_value) && bcd_value == 59);
    assert(!cdm_bcd_to_decimal(0x6A, 60, &bcd_value));

    assert(cdm_receiver_apply(&receiver, empty_frame, strlen(empty_frame), 1788998401) == CDM_ACCEPTED);
    assert(receiver.has_good_frame);
    assert(receiver.sequence == 1u);
    assert(receiver.usage_count == 0u);
    assert(cdm_receiver_apply(&receiver, empty_frame, strlen(empty_frame), 1788998402) == CDM_REJECT_SEQUENCE);
    assert(receiver.sequence == 1u);

    char corrupt[256];
    assert(strlen(empty_frame) + 1 < sizeof(corrupt));
    memcpy(corrupt, empty_frame, strlen(empty_frame) + 1);
    char *crc = strstr(corrupt, "BE8028D7");
    assert(crc != NULL);
    crc[0] = '0';
    assert(cdm_receiver_apply(&receiver, corrupt, strlen(corrupt), 1788998403) == CDM_REJECT_CRC);
    assert(receiver.sequence == 1u);
    assert(cdm_receiver_apply(&receiver, usage_frame, strlen(usage_frame), 1788998400) == CDM_ACCEPTED);
    assert(receiver.sequence == 2u && receiver.usage_count == 1u && receiver.reset_count == 1u);
    assert(receiver.usage[0].window_count == 1u);
    assert(receiver.usage[0].windows[0].has_percent_remaining);
    assert(receiver.usage[0].windows[0].percent_remaining == 58);
    assert(strcmp(receiver.global_resets[0].source, "codex-resets.com") == 0);
    cdm_receiver_update_stale(&receiver, 1788998699);
    assert(!receiver.stale);
    cdm_receiver_update_stale(&receiver, 1788998700);
    assert(receiver.stale);
    assert(receiver.has_good_frame);
    puts("receiver core: CRC, frame acceptance, ordering, last-good retention and stale pass");
    return 0;
}
