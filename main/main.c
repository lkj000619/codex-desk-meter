#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/usb_serial_jtag.h"
#include "esp_timer.h"
#include "esp_log.h"
#include "receiver.h"
#include "board.h"
#include "feature.h"

static const char *TAG="cdm";
static cdm_state state;
static char *line;
static size_t used;
static bool overflow;
static int page;
static bool button_prev;
static bool button_consumed;
static uint64_t button_changed;
static uint64_t last_paint;
static uint64_t last_usage_advance;
static int usage_offset;
static const uint16_t BG=0x08a3, FG=0xffff, MUTED=0xad55, ACCENT=0x3dee, WARN=0xfd20;
static const char *str(const cJSON *o,const char *key,const char *fallback) {
    cJSON *v=cJSON_GetObjectItemCaseSensitive(o,key);
    return cJSON_IsString(v) ? v->valuestring : fallback;
}
static void clipped(char *dst,size_t cap,const char *src,size_t count) { snprintf(dst,cap,"%.*s",(int)count,src); }
static void draw_header(const char *title,uint64_t ms) {
    board_clear(BG); board_rect(0,0,820,48,0x1148); board_text(18,13,title,FG,3);
    char top[64]; snprintf(top,sizeof(top),"%s  SEQ %lu",cdm_stale(&state,ms)?"STALE":"LIVE",(unsigned long)state.sequence);
    board_text(560,17,top,cdm_stale(&state,ms)?WARN:ACCENT,2);
}
static void draw_usage(uint64_t ms) {
    draw_header("USAGE DASHBOARD",ms);
    if(!state.payload) { board_text(30,95,"WAITING FOR PC FIXTURE",WARN,3); return; }
    cJSON *usage=cJSON_GetObjectItemCaseSensitive(state.payload,"usage");
    int total=0;
    for(cJSON *s=usage->child;s;s=s->next) {
        cJSON *wins=cJSON_GetObjectItemCaseSensitive(s,"windows");
        int n=cJSON_GetArraySize(wins); total+=n?n:1;
    }
    if(!total) { board_text(30,95,"NO PROVIDER DATA",WARN,3); return; }
    usage_offset%=total;
    int index=0,shown=0,y=60; char row[170];
    for(cJSON *s=usage->child;s && shown<3;s=s->next) {
        const char *provider=str(s,"provider_id","unknown"), *status=str(s,"status","unknown");
        char name[28]; clipped(name,sizeof(name),provider,22);
        cJSON *wins=cJSON_GetObjectItemCaseSensitive(s,"windows");
        int count=cJSON_GetArraySize(wins); if(!count) count=1;
        cJSON *w=wins?wins->child:NULL;
        for(int item=0;item<count && shown<3;item++,index++) {
            if(index<usage_offset) { if(w) w=w->next; continue; }
            int64_t observed=0;
            bool known=cdm_timestamp(str(s,"observed_at",NULL),&observed) && state.sent_epoch>=observed;
            bool source_stale=known && (uint64_t)(state.sent_epoch-observed)+(ms-state.received_ms)/1000>=300;
            snprintf(row,sizeof(row),"%s  %s%s  AT %.22s",name,status,source_stale?" SOURCE STALE":"",str(s,"observed_at","unknown"));
            board_text(20,y,row,FG,2); y+=22;
            if(!w) { board_text(20,y,"  NO WINDOWS / STATUS ONLY",MUTED,2); y+=43; shown++; continue; }
            cJSON *used=cJSON_GetObjectItemCaseSensitive(w,"percent_used"), *remain=cJSON_GetObjectItemCaseSensitive(w,"percent_remaining");
            cJSON *abs=cJSON_GetObjectItemCaseSensitive(w,"remaining_units");
            const char *label=str(w,"label","window"), *unit=str(w,"unit","unknown");
            if(cJSON_IsNumber(used) && cJSON_IsNumber(remain)) snprintf(row,sizeof(row),"  %.18s  USED %.1f%%  LEFT %.1f%%  UNIT %.8s",label,used->valuedouble,remain->valuedouble,unit);
            else if(cJSON_IsNumber(used)) snprintf(row,sizeof(row),"  %.18s  USED %.1f%%  LEFT UNKNOWN  UNIT %.8s",label,used->valuedouble,unit);
            else if(cJSON_IsNumber(abs)) snprintf(row,sizeof(row),"  %.18s  LEFT %.1f %.8s",label,abs->valuedouble,unit);
            else snprintf(row,sizeof(row),"  %.18s  UNKNOWN  UNIT %.8s",label,unit);
            board_text(20,y,row,MUTED,2); y+=21;
            snprintf(row,sizeof(row),"  RESET %s",str(w,"resets_at","unknown")); board_text(20,y,row,MUTED,2); y+=22;
            y+=8; shown++; w=w->next;
        }
    }
    if(total>3) { snprintf(row,sizeof(row),"AUTO PAGE %d-%d / %d",usage_offset+1,usage_offset+shown,total); board_text(20,294,row,WARN,2); }
}
static void draw_global(uint64_t ms) {
    draw_header("GLOBAL RESET",ms);
    cJSON *globals=state.payload?cJSON_GetObjectItemCaseSensitive(state.payload,"global_resets"):NULL;
    cJSON *g=NULL;
    for(cJSON *item=globals?globals->child:NULL;item;item=item->next)
        if(!strcmp(str(item,"source",""),"codex-resets.com")) { g=item; break; }
    if(!g) { board_text(30,100,"NO RESET HISTORY",WARN,3); board_text(30,155,"SOURCE: codex-resets.com",MUTED,2); return; }
    char row[180];
    snprintf(row,sizeof(row),"SOURCE %s",str(g,"source","unknown")); board_text(30,85,row,FG,3);
    snprintf(row,sizeof(row),"FETCHED %s",str(g,"captured_at","unknown")); board_text(30,130,row,MUTED,2);
    if(cJSON_IsTrue(cJSON_GetObjectItemCaseSensitive(g,"stale"))) board_text(610,132,"STALE",WARN,2);
    const char *latest=str(g,"latest_reset_at",NULL);
    if(latest) { snprintf(row,sizeof(row),"LAST RESET %s",latest); board_text(30,175,row,ACCENT,3); }
    else board_text(30,175,"LAST RESET UNKNOWN",WARN,3);
    int64_t reset_epoch;
    if(latest && cdm_timestamp(latest,&reset_epoch) && state.sent_epoch>=reset_epoch) {
        uint64_t seconds=(uint64_t)(state.sent_epoch-reset_epoch)+(ms-state.received_ms)/1000;
        snprintf(row,sizeof(row),"ELAPSED %llud %02lluh %02llum",(unsigned long long)(seconds/86400),(unsigned long long)(seconds/3600%24),(unsigned long long)(seconds/60%60));
        board_text(30,235,row,ACCENT,2);
    } else board_text(30,235,"ELAPSED UNKNOWN / RESET SCHEDULED",MUTED,2);
}
static void draw_status(uint64_t ms) {
    draw_header("STATUS",ms); char row[150];
    snprintf(row,sizeof(row),"RECEIVER %s",state.has_sequence?"CONNECTED DATA":"NO DATA"); board_text(30,85,row,FG,3);
    snprintf(row,sizeof(row),"FRAME ERROR %s",state.error[0]?state.error:"NONE"); board_text(30,130,row,state.error[0]?WARN:MUTED,2);
    if(state.has_sequence) { snprintf(row,sizeof(row),"LAST GOOD RECEIVE %llu SEC AGO",(unsigned long long)((ms-state.received_ms)/1000)); board_text(30,170,row,MUTED,2); }
    board_text(30,220,"USB 115200 8N1  NO ACK",ACCENT,2);
    board_text(30,265,"BOOT: NEXT PAGE  PC: REFRESH",MUTED,2);
}
static void redraw(uint64_t ms) { if(page==0) draw_usage(ms); else if(page==1) draw_global(ms); else draw_status(ms); board_present(); last_paint=ms; }
static void receive_bytes(uint64_t now_ms) {
    uint8_t input[256]; int n=usb_serial_jtag_read_bytes(input,sizeof(input),pdMS_TO_TICKS(20));
    for(int i=0;i<n;i++) {
        uint8_t ch=input[i];
        if(ch=='\n') {
            if(!overflow && used<CDM_MAX_FRAME) { line[used++]='\n'; bool ok=cdm_accept(&state,line,used,now_ms); ESP_LOGI(TAG,"frame %s seq=%lu error=%s bytes=%u",ok?"accepted":"rejected",(unsigned long)state.sequence,state.error,(unsigned)used); if(ok) { usage_offset=0; last_usage_advance=now_ms; redraw(now_ms); } }
            else { snprintf(state.error,sizeof(state.error),"FRAME_TOO_LONG"); ESP_LOGW(TAG,"frame too long"); }
            used=0; overflow=false;
        } else if(!overflow) { if(used<CDM_MAX_FRAME-1) line[used++]=ch; else overflow=true; }
    }
}
void app_main(void) {
    cdm_init(&state);
    line=malloc(CDM_MAX_FRAME+1);
    if(!line) { ESP_LOGE(TAG,"frame buffer allocation failed"); return; }
    if(!board_start()) { ESP_LOGE(TAG,"LCD initialization failed"); return; }
    usb_serial_jtag_driver_config_t usb={.rx_buffer_size=8192,.tx_buffer_size=2048};
    ESP_ERROR_CHECK(usb_serial_jtag_driver_install(&usb));
    uint64_t ms=esp_timer_get_time()/1000; redraw(ms);
    for(;;) {
        ms=esp_timer_get_time()/1000; receive_bytes(ms);
        bool pressed=board_boot_pressed();
        if(pressed!=button_prev) { button_changed=ms; button_prev=pressed; if(!pressed) button_consumed=false; }
        if(pressed && !button_consumed && ms-button_changed>=40) { page=(page+1)%3; redraw(ms); button_consumed=true; }
        feature_idle_dimming(ms,state.received_ms,state.has_sequence);
        if(page==0 && state.has_sequence && ms-last_usage_advance>=5000) { usage_offset+=3; last_usage_advance=ms; redraw(ms); }
        if(ms-last_paint>=1000) redraw(ms);
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}
