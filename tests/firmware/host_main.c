#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "cdm.h"
#include "legacy.h"
#include "gui.h"
#include "bsp.h"

static uint16_t image_pixels[820*320];
void bsp_pixel(int x,int y,uint16_t color)
{ if (x>=0 && x<820 && y>=0 && y<320) image_pixels[y*820+x]=color; }
void bsp_fill(int x,int y,int width,int height,uint16_t color)
{
    for(int yy=y;yy<y+height;yy++) for(int xx=x;xx<x+width;xx++) bsp_pixel(xx,yy,color);
}
int bsp_boot_level(void) { return 1; }
esp_err_t bsp_init(void) { return 0; }

static void save_ppm(const char *prefix,const char *screen,unsigned page)
{
    if (!prefix) return;
    char path[512];
    if (snprintf(path,sizeof path,"%s-%s-%u.ppm",prefix,screen,page)>=(int)sizeof path) return;
    FILE *file=fopen(path,"wb"); if (!file) return;
    fprintf(file,"P6\n820 320\n255\n");
    for(size_t i=0;i<820*320;i++) {
        uint16_t value=image_pixels[i];
        unsigned char rgb[3]={ (unsigned char)(((value>>11)&31)*255/31),
            (unsigned char)(((value>>5)&63)*255/63), (unsigned char)((value&31)*255/31) };
        fwrite(rgb,1,3,file);
    }
    fclose(file);
}

static cJSON *render_state(const cdm_state *state,uint64_t now,const char *prefix)
{
    cJSON *result=cJSON_CreateObject(), *pages=cJSON_CreateArray();
    gui_control control={.connected=true};
    cJSON_AddNumberToObject(result,"quota_count",gui_quota_count(state));
    unsigned count=0;
    do {
        gui_render(state,&control,now,false,0);
        cJSON_AddItemToArray(pages,cJSON_CreateNumber(cdm_crc32((const unsigned char *)image_pixels,sizeof image_pixels)));
        save_ppm(prefix,"usage",count++);
        gui_next_window_page(&control,state);
    } while (control.quota_page && count<1024);
    cJSON_AddItemToObject(result,"usage_pages",pages);
    gui_short_press(&control); gui_render(state,&control,now,false,0);
    cJSON_AddNumberToObject(result,"global",cdm_crc32((const unsigned char *)image_pixels,sizeof image_pixels));
    save_ppm(prefix,"global",0);
    gui_short_press(&control); gui_render(state,&control,now,false,0);
    cJSON_AddNumberToObject(result,"status",cdm_crc32((const unsigned char *)image_pixels,sizeof image_pixels));
    save_ppm(prefix,"status",0);
    gui_short_press(&control); gui_render(state,&control,now,false,0);
    cJSON_AddBoolToObject(result,"screen_wrap",control.screen==0 && control.quota_page==0);
    return result;
}

static char *read_input(void)
{
    size_t cap=4096,n=0; char *data=malloc(cap);
    if (!data) return NULL;
    int c; while((c=fgetc(stdin))!=EOF) {
        if (n+1>=cap) { cap*=2; char *more=realloc(data,cap); if (!more) { free(data); return NULL; } data=more; }
        data[n++]=(char)c;
    }
    data[n]=0; return data;
}
static cJSON *wire_event(cdm_state *state,const cJSON *event)
{
    const cJSON *line=cJSON_GetObjectItemCaseSensitive(event,"line"), *mono=cJSON_GetObjectItemCaseSensitive(event,"mono_ms"),
        *now=cJSON_GetObjectItemCaseSensitive(event,"now_ms"), *hex=cJSON_GetObjectItemCaseSensitive(event,"line_hex");
    if ((!cJSON_IsString(line) && !cJSON_IsString(hex)) || !cJSON_IsNumber(mono)) return NULL;
    unsigned char *bytes=NULL; size_t length=0;
    if (cJSON_IsString(hex)) {
        size_t n=strlen(hex->valuestring); if (n%2) return NULL;
        bytes=malloc(n/2); if (!bytes) return NULL;
        for(size_t i=0;i<n;i+=2) {
            unsigned value; if (sscanf(hex->valuestring+i,"%2x",&value)!=1) { free(bytes); return NULL; }
            bytes[length++]=(unsigned char)value;
        }
    } else { bytes=(unsigned char *)line->valuestring; length=strlen(line->valuestring); }
    bool accepted=cdm_accept(state,bytes,length,(uint64_t)mono->valuedouble);
    if (cJSON_IsString(hex)) free(bytes);
    uint64_t at=cJSON_IsNumber(now)?(uint64_t)now->valuedouble:(uint64_t)mono->valuedouble;
    cJSON *out=cJSON_CreateObject(), *usage=cJSON_CreateArray(), *global=cJSON_CreateArray();
    cJSON_AddBoolToObject(out,"accepted",accepted);
    cJSON_AddBoolToObject(out,"has_sequence",state->has_sequence);
    if (state->has_sequence) cJSON_AddNumberToObject(out,"sequence",state->sequence);
    else cJSON_AddNullToObject(out,"sequence");
    cJSON_AddStringToObject(out,"error",state->wire_error);
    cJSON_AddBoolToObject(out,"anchor",state->has_anchor);
    uint64_t age;
    if (cdm_receive_age(state,at,&age)) cJSON_AddNumberToObject(out,"receive_age_s",age);
    else cJSON_AddNullToObject(out,"receive_age_s");
    for(size_t i=0;i<state->usage_count;i++) {
        cdm_entry *e=&state->usage[i]; cJSON *item=cJSON_CreateObject();
        cJSON_AddStringToObject(item,"key",e->key);
        cJSON_AddItemToObject(item,"current",cJSON_Duplicate(e->current,1));
        cJSON_AddItemToObject(item,"good",e->good?cJSON_Duplicate(e->good,1):cJSON_CreateNull());
        const cJSON *display=e->good?e->good:e->current;
        if (cdm_source_age(state,display,at,&age)) cJSON_AddNumberToObject(item,"source_age_s",age);
        else cJSON_AddNullToObject(item,"source_age_s");
        cJSON_AddBoolToObject(item,"stale",cdm_stale(state,display,at));
        cJSON_AddItemToArray(usage,item);
    }
    for(size_t i=0;i<state->global_count;i++) {
        cdm_entry *e=&state->global[i]; cJSON *item=cJSON_CreateObject();
        cJSON_AddStringToObject(item,"key",e->key);
        cJSON_AddItemToObject(item,"current",cJSON_Duplicate(e->current,1));
        cJSON_AddItemToObject(item,"good",e->good?cJSON_Duplicate(e->good,1):cJSON_CreateNull());
        cJSON_AddItemToArray(global,item);
    }
    cJSON_AddItemToObject(out,"usage",usage);
    cJSON_AddItemToObject(out,"global",global);
    if (cJSON_IsTrue(cJSON_GetObjectItemCaseSensitive(event,"render"))) {
        const cJSON *prefix=cJSON_GetObjectItemCaseSensitive(event,"ppm_prefix");
        cJSON_AddItemToObject(out,"render",render_state(state,at,cJSON_IsString(prefix)?prefix->valuestring:NULL));
    }
    return out;
}
int main(int argc,char **argv)
{
    char *input=read_input(); if (!input) return 2;
    cJSON *request=cJSON_Parse(input); free(input);
    if (!request) return 2;
    cJSON *result=NULL;
    if (argc>1 && !strcmp(argv[1],"--wire")) {
        const cJSON *events=cJSON_GetObjectItemCaseSensitive(request,"events");
        if (cJSON_IsArray(events)) {
            cdm_state state; cdm_init(&state); result=cJSON_CreateArray();
            for(const cJSON *e=events->child;e;e=e->next) {
                cJSON *r=wire_event(&state,e);
                if (!r) { cJSON_Delete(result); result=NULL; break; }
                cJSON_AddItemToArray(result,r);
            }
            cdm_free(&state);
        }
    } else result=cdm_legacy_run(request);
    cJSON_Delete(request);
    if (!result) return 2;
    char *json=cJSON_PrintUnformatted(result); cJSON_Delete(result);
    if (!json) return 2;
    puts(json); free(json); return 0;
}
