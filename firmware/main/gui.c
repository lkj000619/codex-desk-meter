#include "gui.h"
#include "bsp.h"
#include <ctype.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

#define PAPER 0xF7BE
#define INK 0x18C3
#define RULE 0xD6BA
#define BLUE 0x0438
#define AMBER 0xFBE0
#define RED 0xB1A6
#define MUTED 0x7BEF

// 5x7 uppercase bitmap, rendered at integer scale; no font service or heap allocation.
static const struct { char ch; unsigned char rows[7]; } font[] = {
 {'A',{14,17,17,31,17,17,17}}, {'B',{30,17,17,30,17,17,30}},
 {'C',{14,17,16,16,16,17,14}}, {'D',{30,17,17,17,17,17,30}},
 {'E',{31,16,16,30,16,16,31}}, {'F',{31,16,16,30,16,16,16}},
 {'G',{14,17,16,23,17,17,14}}, {'H',{17,17,17,31,17,17,17}},
 {'I',{31,4,4,4,4,4,31}}, {'J',{7,2,2,2,18,18,12}},
 {'K',{17,18,20,24,20,18,17}}, {'L',{16,16,16,16,16,16,31}},
 {'M',{17,27,21,21,17,17,17}}, {'N',{17,25,21,19,17,17,17}},
 {'O',{14,17,17,17,17,17,14}}, {'P',{30,17,17,30,16,16,16}},
 {'Q',{14,17,17,17,21,18,13}}, {'R',{30,17,17,30,20,18,17}},
 {'S',{15,16,16,14,1,1,30}}, {'T',{31,4,4,4,4,4,4}},
 {'U',{17,17,17,17,17,17,14}}, {'V',{17,17,17,17,17,10,4}},
 {'W',{17,17,17,21,21,21,10}}, {'X',{17,17,10,4,10,17,17}},
 {'Y',{17,17,10,4,4,4,4}}, {'Z',{31,1,2,4,8,16,31}},
 {'0',{14,17,19,21,25,17,14}}, {'1',{4,12,4,4,4,4,14}},
 {'2',{14,17,1,2,4,8,31}}, {'3',{30,1,1,14,1,1,30}},
 {'4',{2,6,10,18,31,2,2}}, {'5',{31,16,30,1,1,17,14}},
 {'6',{6,8,16,30,17,17,14}}, {'7',{31,1,2,4,8,8,8}},
 {'8',{14,17,17,14,17,17,14}}, {'9',{14,17,17,15,1,2,12}},
 {'.',{0,0,0,0,0,12,12}}, {':',{0,12,12,0,12,12,0}},
 {'-',{0,0,0,31,0,0,0}}, {'_',{0,0,0,0,0,0,31}},
 {'/',{1,1,2,4,8,16,16}}, {'%',{17,18,2,4,8,9,17}},
 {'+',{0,4,4,31,4,4,0}}, {'(',{2,4,8,8,8,4,2}},
 {')',{8,4,2,2,2,4,8}}, {'=',{0,0,31,0,31,0,0}},
 {'?',{14,17,1,2,4,0,4}}, {'#',{10,10,31,10,31,10,10}}
};
static void draw_text(int x,int y,int width,int scale,uint16_t color,const char *value)
{
    if (!value || width<6*scale) return;
    int n=0, limit=width/(6*scale);
    for(const unsigned char *p=(const unsigned char *)value;*p && n<limit;p++,n++) {
        int ch=toupper(*p);
        if (ch==' ') continue;
        const unsigned char *rows=NULL;
        for(size_t i=0;i<sizeof font/sizeof font[0];i++) if (font[i].ch==ch) { rows=font[i].rows; break; }
        if (!rows) rows=font[sizeof font/sizeof font[0]-1].rows;
        for(int r=0;r<7;r++) for(int c=0;c<5;c++) if (rows[r]&(1<<(4-c)))
            bsp_fill(x+n*6*scale+c*scale,y+r*scale,scale,scale,color);
    }
}
static const cJSON *field(const cJSON *v,const char *name)
{ return cJSON_GetObjectItemCaseSensitive(v,name); }
static const char *string(const cJSON *v)
{ return cJSON_IsString(v)?v->valuestring:NULL; }
static const char *or_dash(const char *v) { return v?v:"--"; }
static bool value_is(const cJSON *v,const char *name,const char *word)
{ const char *s=string(field(v,name)); return s && !strcmp(s,word); }
static int number(const cJSON *v,char *out,size_t size,const char *unit,const char *prefix,int width,int scale)
{
    int len;
    if (cJSON_IsNumber(v) && isfinite(v->valuedouble)) {
        double value=v->valuedouble;
        len=value==floor(value)?snprintf(out,size,"%s%.0f%s",prefix,value,unit):width/6+1;
        if (len<0 || len>width/6 || len>=(int)size)
            len=snprintf(out,size,"%s%.7g%s",prefix,value,unit);
    } else len=snprintf(out,size,"%s--",prefix);
    if (len<0 || len>width/6 || len>=(int)size)
        len=snprintf(out,size,"%s--",prefix);
    while (scale>1 && len>width/(6*scale)) scale--;
    return scale;
}
static void time_text(const char *value,char *out,size_t size)
{ snprintf(out,size,"%s",value?value:"--"); }
static void rule(int x,int y,int w) { bsp_fill(x,y,w,1,RULE); }
static const cJSON *visible(const cdm_entry *e,bool *last_good)
{
    *last_good=false;
    if (!e) return NULL;
    if ((value_is(e->current,"status","error") || value_is(e->current,"status","unauthorized")) && e->good) {
        *last_good=true; return e->good;
    }
    return e->current;
}
static size_t count_kind(const cdm_state *state,bool quota)
{
    size_t count=0;
    for(size_t i=0;i<state->usage_count;i++) {
        bool old; const cJSON *r=visible(&state->usage[i],&old);
        if (!value_is(r,"metric_kind",quota?"quota_window":"session_telemetry")) continue;
        if (!quota) count++;
        else { const cJSON *w=field(r,"windows"); if (cJSON_IsArray(w)) count+=cJSON_GetArraySize(w); }
    }
    return count;
}
size_t gui_quota_count(const cdm_state *state) { return count_kind(state,true); }
static size_t pages(const cdm_state *state)
{
    size_t q=(count_kind(state,true)+1)/2,s=count_kind(state,false);
    return q>s?q:s?s:1;
}
void gui_next_window_page(gui_control *control,const cdm_state *state)
{ control->quota_page=(control->quota_page+1)%pages(state); }
void gui_short_press(gui_control *control)
{ control->screen=(control->screen+1)%3; }
static const cJSON *quota_at(const cdm_state *state,size_t index,const cJSON **record,bool *last_good)
{
    for(size_t i=0;i<state->usage_count;i++) {
        const cJSON *r=visible(&state->usage[i],last_good);
        if (!value_is(r,"metric_kind","quota_window")) continue;
        const cJSON *windows=field(r,"windows");
        for(const cJSON *w=windows?windows->child:NULL;w;w=w->next)
            if (!index--) { *record=r; return w; }
    }
    return NULL;
}
static const cJSON *session_at(const cdm_state *state,size_t index,bool *last_good)
{
    for(size_t i=0;i<state->usage_count;i++) {
        const cJSON *r=visible(&state->usage[i],last_good);
        if (value_is(r,"metric_kind","session_telemetry") && !index--) return r;
    }
    return NULL;
}
static const cJSON *channel(const cJSON *record,const char *id)
{
    const cJSON *windows=field(record,"windows");
    for(const cJSON *w=windows?windows->child:NULL;w;w=w->next)
        if (value_is(w,"window_id",id)) return field(w,"used_units");
    return NULL;
}
static void quota_card(const cdm_state *state,size_t index,int y,uint64_t now)
{
    const cJSON *r=NULL; bool old=false;
    const cJSON *w=quota_at(state,index,&r,&old);
    if (!w) { draw_text(18,y+28,395,2,MUTED,state->has_frame?"NO WINDOW":"WAITING / NO CACHE"); return; }
    char line[100],used[32],remaining[32],when[40];
    snprintf(line,sizeof line,"%s / %s",or_dash(string(field(r,"provider_id"))),or_dash(string(field(w,"label"))));
    draw_text(18,y,390,2,INK,line);
    snprintf(line,sizeof line,"ID %s  %s%s",or_dash(string(field(w,"window_id"))),or_dash(string(field(w,"unit"))),old?" LAST GOOD":"");
    draw_text(18,y+18,390,1,MUTED,line);
    const cJSON *percent_used=field(w,"percent_used"),*percent_remaining=field(w,"percent_remaining");
    int used_scale=number(cJSON_IsNumber(percent_used)?percent_used:field(w,"used_units"),used,sizeof used,
                          cJSON_IsNumber(percent_used)?"%":"","",170,3);
    int remaining_scale=number(cJSON_IsNumber(percent_remaining)?percent_remaining:field(w,"remaining_units"),
                               remaining,sizeof remaining,cJSON_IsNumber(percent_remaining)?"%":"","USED / REM ",215,2);
    draw_text(18,y+34,170,used_scale,INK,used);
    draw_text(190,y+39,215,remaining_scale,INK,remaining);
    bsp_fill(18,y+63,386,5,RULE);
    const cJSON *percent=field(w,"percent_used");
    if (cJSON_IsNumber(percent)) bsp_fill(18,y+63,(int)(percent->valuedouble*3.86),5,INK);
    time_text(string(field(w,"resets_at")),when,sizeof when);
    snprintf(line,sizeof line,"RESET %s",when); draw_text(18,y+71,390,1,INK,line);
    time_text(string(field(r,"observed_at")),when,sizeof when);
    snprintf(line,sizeof line,"OBS %s%s",when,cdm_stale(state,r,now)?" STALE":"");
    draw_text(18,y+82,390,1,cdm_stale(state,r,now)?AMBER:MUTED,line);
}
static void session_row(int y,const char *label,const cJSON *v,uint16_t color)
{
    char value[32]; int scale=number(v,value,sizeof value,"","",125,2);
    draw_text(440,y,240,2,color,label); draw_text(680,y,125,scale,color,value); rule(440,y+18,363);
}
static void usage_screen(const cdm_state *state,const gui_control *control,uint64_t now)
{
    size_t page=control->quota_page%pages(state), q=count_kind(state,true),s=count_kind(state,false);
    char line[100];
    draw_text(18,53,260,2,INK,"ACCOUNT QUOTA WINDOWS");
    if (q) snprintf(line,sizeof line,"WIN %u-%u / %u",(unsigned)(page*2+1),(unsigned)(page*2+2<q?page*2+2:q),(unsigned)q);
    else snprintf(line,sizeof line,"WIN 0 / 0");
    draw_text(286,56,130,1,MUTED,line);
    quota_card(state,page*2,75,now); rule(18,172,390); quota_card(state,page*2+1,181,now);
    bsp_fill(425,52,1,240,RULE);
    draw_text(440,53,275,2,INK,"SESSION TELEMETRY");
    bool old=false; const cJSON *r=session_at(state,s?page%s:0,&old);
    if (!r) { draw_text(440,100,360,3,MUTED,state->has_frame?"NO SESSION":"WAITING"); return; }
    snprintf(line,sizeof line,"%s %u/%u%s",or_dash(string(field(r,"snapshot_id"))),(unsigned)(page%s+1),(unsigned)s,old?" LAST GOOD":"");
    draw_text(440,72,363,1,MUTED,line);
    char total[32]; int total_scale=number(channel(r,"normalized_total"),total,sizeof total,"","",160,3);
    draw_text(440,90,218,2,INK,"TOTAL IN+OUT"); draw_text(643,86,160,total_scale,INK,total);
    session_row(119,"INPUT",channel(r,"input"),INK);
    session_row(144,"OUTPUT",channel(r,"output"),INK);
    session_row(169,"CACHED INPUT*",channel(r,"cached_input"),BLUE);
    session_row(194,"REASONING*",channel(r,"reasoning_output"),BLUE);
    session_row(219,"SOURCE TOTAL",channel(r,"source_total"),INK);
    draw_text(440,246,363,1,MUTED,"* INCLUDED SUBSETS. LIMIT/REM/% UNKNOWN");
    time_text(string(field(r,"observed_at")),line,sizeof line); draw_text(440,260,363,1,cdm_stale(state,r,now)?AMBER:MUTED,line);
    draw_text(440,272,363,1,MUTED,"ACCOUNT QUOTA SEPARATE");
}
static const cdm_entry *global_entry(const cdm_state *state)
{
    for(size_t i=0;i<state->global_count;i++) if (!strcmp(state->global[i].key,"codex-resets.com")) return &state->global[i];
    return NULL;
}
static void global_screen(const cdm_state *state,uint64_t now)
{
    const cdm_entry *e=global_entry(state); const cJSON *current=e?e->current:NULL;
    bool latest=current && cJSON_IsNull(field(current,"error_code")) && !cJSON_IsTrue(field(current,"stale")) && cJSON_IsString(field(current,"latest_reset_at"));
    const cJSON *record=latest?current:e?e->good:NULL;
    draw_text(22,55,550,3,INK,"GLOBAL CODEX RESET"); draw_text(570,61,235,2,MUTED,"CODEX-RESETS.COM"); rule(22,88,776);
    if (!record) { draw_text(22,112,700,4,MUTED,"DEFAULT / NO CACHE"); draw_text(22,165,700,2,MUTED,"ELAPSED UNKNOWN"); return; }
    draw_text(22,98,450,2,latest?BLUE:AMBER,latest?"LATEST OBSERVATION":"LAST KNOWN");
    const char *reset=string(field(record,"latest_reset_at")); char line[100];
    time_text(reset,line,sizeof line); draw_text(22,124,780,3,INK,line);
    int64_t reset_us;
    bool clock=state->has_anchor && now>=state->anchor_mono_ms && reset && cdm_parse_time(reset,&reset_us) &&
        state->anchor_utc_us+(int64_t)(now-state->anchor_mono_ms)*1000>=reset_us;
    if (clock) {
        uint64_t elapsed=(uint64_t)((state->anchor_utc_us+(int64_t)(now-state->anchor_mono_ms)*1000-reset_us)/1000000);
        snprintf(line,sizeof line,"%lluh %llum ELAPSED",(unsigned long long)(elapsed/3600),(unsigned long long)(elapsed/60%60));
    } else snprintf(line,sizeof line,"ELAPSED UNKNOWN");
    draw_text(22,167,780,3,INK,line);
    time_text(string(field(record,"captured_at")),line,sizeof line);
    draw_text(22,215,780,2,MUTED,"SOURCE CAPTURED AT"); draw_text(22,238,780,2,INK,line);
    draw_text(22,272,780,1,MUTED,"INDEPENDENT OF PERSONAL QUOTA RESET");
}
static void age_text(const cdm_state *state,const cJSON *record,uint64_t now,bool source,char *out,size_t size)
{
    uint64_t seconds; bool known=source?cdm_source_age(state,record,now,&seconds):cdm_receive_age(state,now,&seconds);
    if (known) snprintf(out,size,"%llus",(unsigned long long)seconds); else snprintf(out,size,"UNKNOWN");
}
static void status_screen(const cdm_state *state,const gui_control *control,uint64_t now,bool temp_known,float temp)
{
    draw_text(22,55,760,3,INK,"SYSTEM STATUS"); rule(22,86,776);
    char line[100],value[40];
    draw_text(22,102,330,2,MUTED,"USB LINK"); draw_text(380,102,400,2,control->connected?BLUE:RED,control->connected?"CONNECTED":"DISCONNECTED");
    age_text(state,NULL,now,false,value,sizeof value);
    draw_text(22,132,330,2,MUTED,"RECEIVE AGE"); draw_text(380,132,400,2,INK,value);
    const cJSON *observed=NULL;
    for(size_t i=0;i<state->usage_count;i++) { bool old; const cJSON *r=visible(&state->usage[i],&old); if (cJSON_IsString(field(r,"observed_at"))) { observed=r; break; } }
    age_text(state,observed,now,true,value,sizeof value);
    draw_text(22,162,330,2,MUTED,"SOURCE AGE"); draw_text(380,162,400,2,cdm_stale(state,observed,now)?AMBER:INK,value);
    time_text(string(field(observed,"observed_at")),line,sizeof line);
    draw_text(22,192,330,2,MUTED,"ORIGINAL OBS"); draw_text(380,192,400,2,INK,line);
    draw_text(22,222,330,2,MUTED,"FRAME / CRC"); draw_text(380,222,400,2,state->wire_error[0]?RED:INK,state->wire_error[0]?state->wire_error:state->has_frame?"VALID":"WAITING");
    if (temp_known) snprintf(value,sizeof value,"%.1f C",temp); else snprintf(value,sizeof value,"UNKNOWN");
    draw_text(22,252,330,2,MUTED,"CHIP TEMPERATURE"); draw_text(380,252,400,2,INK,value);
}
void gui_render(const cdm_state *state,const gui_control *control,uint64_t now,bool temp_known,float temp)
{
    bsp_fill(0,0,820,320,PAPER); bsp_fill(0,0,820,32,INK);
    draw_text(12,9,335,2,PAPER,"CODEX DESK METER / STUDIO");
    const char *tabs[]={"1 USAGE","2 GLOBAL","3 STATUS"};
    for(int i=0;i<3;i++) draw_text(365+i*106,10,102,1,(unsigned)i==control->screen?PAPER:MUTED,tabs[i]);
    const char *banner=NULL; uint16_t banner_color=AMBER;
    if (!state->has_frame) banner="WAITING / NO CACHE";
    else if (state->wire_error[0]) { banner=state->wire_error; banner_color=RED; }
    else if (!control->connected) { banner="LINK DISCONNECTED / LAST GOOD IF AVAILABLE"; banner_color=RED; }
    else for(size_t i=0;i<state->usage_count;i++) {
        bool old; const cJSON *r=visible(&state->usage[i],&old);
        if (value_is(state->usage[i].current,"status","error")) { banner="SOURCE ERROR / LAST GOOD IF AVAILABLE"; banner_color=RED; break; }
        if (cdm_stale(state,r,now)) banner="SOURCE STALE / ORIGINAL OBS RETAINED";
    }
    if (banner) { bsp_fill(0,33,820,16,banner_color); draw_text(12,37,795,1,INK,banner); } else rule(0,49,820);
    if (control->screen==1) global_screen(state,now);
    else if (control->screen==2) status_screen(state,control,now,temp_known,temp);
    else usage_screen(state,control,now);
    bsp_fill(0,296,820,24,INK);
    char source[32],received[32],footer[160]; const cJSON *r=NULL;
    for(size_t i=0;i<state->usage_count;i++) { bool old; r=visible(&state->usage[i],&old); if (r) break; }
    age_text(state,r,now,true,source,sizeof source); age_text(state,NULL,now,false,received,sizeof received);
    snprintf(footer,sizeof footer,"SOURCE AGE %s   RECEIVE AGE %s   BOOT: SCREEN / HOLD: WINDOWS",source,received);
    draw_text(12,303,795,1,PAPER,footer);
}
