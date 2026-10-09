#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "cdm.h"
#include "legacy.h"

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
