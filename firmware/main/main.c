#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include "bsp.h"
#include "cdm.h"
#include "gui.h"
#include "f9_temp.h"
#include "driver/usb_serial_jtag.h"
#include "esp_heap_caps.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"

static cdm_state state;
static SemaphoreHandle_t state_mutex;
static volatile bool dirty=true;

static uint64_t monotonic_ms(void) { return (uint64_t)(esp_timer_get_time()/1000); }

static void receiver_task(void *unused)
{
    unsigned char *line=heap_caps_malloc(CDM_MAX_FRAME,MALLOC_CAP_SPIRAM|MALLOC_CAP_8BIT);
    if (!line) abort();
    size_t length=0; bool overflow=false;
    for (;;) {
        unsigned char incoming[128];
        int count=usb_serial_jtag_read_bytes(incoming,sizeof incoming,pdMS_TO_TICKS(20));
        for(int i=0;i<count;i++) {
            unsigned char byte=incoming[i];
            if (!overflow && length<CDM_MAX_FRAME) line[length++]=byte;
            else overflow=true;
            if (byte=='\n') {
                xSemaphoreTake(state_mutex,portMAX_DELAY);
                if (overflow) snprintf(state.wire_error,sizeof state.wire_error,"FRAME_OVERSIZED");
                else cdm_accept(&state,line,length,monotonic_ms());
                dirty=true;
                xSemaphoreGive(state_mutex);
                overflow=false; length=0;
            }
        }
    }
}

void app_main(void)
{
    cdm_init(&state);
    state_mutex=xSemaphoreCreateMutex();
    if (!state_mutex) abort();
    ESP_ERROR_CHECK(bsp_init());
    f9_temp_init();
    usb_serial_jtag_driver_config_t usb={.rx_buffer_size=2048,.tx_buffer_size=256};
    ESP_ERROR_CHECK(usb_serial_jtag_driver_install(&usb));
    if (xTaskCreate(receiver_task,"cdm_rx",6144,NULL,5,NULL)!=pdPASS) abort();

    gui_control control={0};
    int raw=bsp_boot_level(),stable=raw; unsigned same=0;
    uint64_t pressed_at=0, last_draw=0; bool long_fired=false;
    for (;;) {
        uint64_t now=monotonic_ms();
        int sample=bsp_boot_level();
        if (sample==raw) { if (same<3) same++; }
        else { raw=sample; same=0; }
        if (same>=3 && stable!=raw) {
            stable=raw;
            if (!stable) { pressed_at=now; long_fired=false; }
            else if (!long_fired && pressed_at) { gui_short_press(&control); dirty=true; }
        }
        if (!stable && !long_fired && pressed_at && now-pressed_at>=600) {
            xSemaphoreTake(state_mutex,portMAX_DELAY);
            gui_next_window_page(&control,&state);
            xSemaphoreGive(state_mutex);
            long_fired=true; dirty=true;
        }
        bool connected=usb_serial_jtag_is_connected();
        if (connected!=control.connected) { control.connected=connected; dirty=true; }
        if (dirty || now-last_draw>=1000) {
            float temperature=0; bool known=f9_temp_read(&temperature);
            xSemaphoreTake(state_mutex,portMAX_DELAY);
            gui_render(&state,&control,now,known,temperature);
            ESP_ERROR_CHECK(bsp_present());
            dirty=false;
            xSemaphoreGive(state_mutex);
            last_draw=now;
        }
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}
